"""One-time tool: validate and correct zone center coordinates in zone_graph.json.

Run from the project root:
    python tools/validate_zones.py

Click the map to reposition a zone's center, then click Approve.
Use Previous/Next to navigate. Save & Exit writes changes to zone_graph.json.
"""

import json
import sys
from pathlib import Path

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor, QPainter, QPen, QPixmap
from PySide6.QtWidgets import (
    QApplication,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

PROJECT_ROOT = Path(__file__).resolve().parents[1]
ZONE_GRAPH_PATH = PROJECT_ROOT / "zone_graph.json"
MAP_IMAGE_PATH = PROJECT_ROOT / "zone_map.png"
MAP_W, MAP_H = 2700, 1550


def load_data():
    data = json.loads(ZONE_GRAPH_PATH.read_text(encoding="utf-8"))
    nodes = data["nodes"]
    aliases_raw = data.get("aliases", {})

    # Invert alias map: canonical → [log names...]
    alias_index: dict[str, list[str]] = {}
    for log_name, canonical in aliases_raw.items():
        alias_index.setdefault(canonical, []).append(log_name)

    zones = sorted(nodes.keys())
    return data, nodes, alias_index, zones


class ClickableMapLabel(QLabel):
    """QLabel that emits map-space coordinates when clicked."""

    map_clicked = Signal(int, int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._source_pixmap: QPixmap | None = None
        self.setMinimumSize(800, 460)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.setAlignment(Qt.AlignCenter)
        self.setCursor(Qt.CrossCursor)

    def set_source_pixmap(self, pixmap: QPixmap):
        self._source_pixmap = pixmap
        self._refresh()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._refresh()

    def _image_rect(self):
        """Returns (x_offset, y_offset, displayed_w, displayed_h) of the image within the label."""
        if self._source_pixmap is None:
            return 0, 0, self.width(), self.height()
        lw, lh = self.width(), self.height()
        iw, ih = self._source_pixmap.width(), self._source_pixmap.height()
        scale = min(lw / iw, lh / ih)
        dw = int(iw * scale)
        dh = int(ih * scale)
        ox = (lw - dw) // 2
        oy = (lh - dh) // 2
        return ox, oy, dw, dh

    def _refresh(self):
        if self._source_pixmap is None:
            return
        ox, oy, dw, dh = self._image_rect()
        scaled = self._source_pixmap.scaled(dw, dh, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        # Place scaled image centered in a label-sized pixmap
        canvas = QPixmap(self.width(), self.height())
        canvas.fill(QColor(0, 0, 0))
        painter = QPainter(canvas)
        painter.drawPixmap(ox, oy, scaled)
        painter.end()
        self.setPixmap(canvas)

    def mousePressEvent(self, event):
        if self._source_pixmap is None or event.button() != Qt.LeftButton:
            return
        ox, oy, dw, dh = self._image_rect()
        lx = event.position().x() - ox
        ly = event.position().y() - oy
        if 0 <= lx <= dw and 0 <= ly <= dh:
            mx = int(lx * MAP_W / dw)
            my = int(ly * MAP_H / dh)
            mx = max(0, min(MAP_W - 1, mx))
            my = max(0, min(MAP_H - 1, my))
            self.map_clicked.emit(mx, my)


def make_crosshair_pixmap(base_pixmap: QPixmap, cx: int, cy: int) -> QPixmap:
    """Returns a copy of base_pixmap with a red crosshair drawn at (cx, cy) in map coords."""
    w, h = base_pixmap.width(), base_pixmap.height()
    # Scale map coords to pixmap coords
    px = int(cx * w / MAP_W)
    py = int(cy * h / MAP_H)

    result = QPixmap(base_pixmap)
    painter = QPainter(result)
    pen = QPen(QColor(255, 30, 30), 2)
    painter.setPen(pen)
    painter.drawLine(0, py, w, py)
    painter.drawLine(px, 0, px, h)
    pen2 = QPen(QColor(255, 30, 30), 2)
    painter.setPen(pen2)
    painter.drawEllipse(px - 10, py - 10, 20, 20)
    painter.end()
    return result


class ZoneValidatorWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Zone Center Validator")

        self._data, self._nodes, self._alias_index, self._zones = load_data()
        self._working: dict[str, list[int]] = {
            name: list(self._nodes[name]["center"]) for name in self._zones
        }
        self._pending: dict[str, list[int] | None] = {name: None for name in self._zones}
        self._modified: set[str] = set()

        self._base_pixmap = QPixmap(str(MAP_IMAGE_PATH))
        self._index = 0

        self._build_ui()
        self._show_zone(0)
        self.resize(1400, 820)

    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        root = QHBoxLayout(central)
        root.setContentsMargins(4, 4, 4, 4)
        root.setSpacing(8)

        # --- Map ---
        self._map_label = ClickableMapLabel()
        self._map_label.map_clicked.connect(self._on_map_click)
        root.addWidget(self._map_label, stretch=1)

        # --- Side panel ---
        side = QWidget()
        side.setFixedWidth(270)
        side_layout = QVBoxLayout(side)
        side_layout.setContentsMargins(4, 4, 4, 4)
        side_layout.setSpacing(6)

        self._progress_label = QLabel()
        self._progress_label.setAlignment(Qt.AlignCenter)
        side_layout.addWidget(self._progress_label)

        self._zone_name_label = QLabel()
        self._zone_name_label.setWordWrap(True)
        self._zone_name_label.setStyleSheet("font-size: 15px; font-weight: bold;")
        side_layout.addWidget(self._zone_name_label)

        self._aliases_label = QLabel()
        self._aliases_label.setWordWrap(True)
        self._aliases_label.setStyleSheet("color: #555; font-size: 12px;")
        side_layout.addWidget(self._aliases_label)

        self._coords_label = QLabel()
        self._coords_label.setStyleSheet("font-family: monospace; font-size: 12px;")
        side_layout.addWidget(self._coords_label)

        self._pending_label = QLabel()
        self._pending_label.setStyleSheet("font-family: monospace; font-size: 12px; color: #cc6600;")
        side_layout.addWidget(self._pending_label)

        side_layout.addStretch()

        self._approve_btn = QPushButton("✓  Approve")
        self._approve_btn.setStyleSheet("font-size: 14px; padding: 6px;")
        self._approve_btn.clicked.connect(self._approve)
        side_layout.addWidget(self._approve_btn)

        nav = QHBoxLayout()
        self._prev_btn = QPushButton("← Prev")
        self._prev_btn.clicked.connect(self._prev)
        self._next_btn = QPushButton("Next →")
        self._next_btn.clicked.connect(self._next)
        nav.addWidget(self._prev_btn)
        nav.addWidget(self._next_btn)
        side_layout.addLayout(nav)

        self._save_btn = QPushButton("Save & Exit")
        self._save_btn.setStyleSheet("font-size: 13px; padding: 5px; color: darkgreen; font-weight: bold;")
        self._save_btn.clicked.connect(self._save)
        side_layout.addWidget(self._save_btn)

        self._status_label = QLabel("")
        self._status_label.setWordWrap(True)
        self._status_label.setStyleSheet("color: green; font-size: 11px;")
        side_layout.addWidget(self._status_label)

        root.addWidget(side)

    def _show_zone(self, index: int):
        self._index = index
        name = self._zones[index]
        cx, cy = self._working[name]

        # Draw crosshair
        crosshair = make_crosshair_pixmap(self._base_pixmap, cx, cy)
        self._map_label.set_source_pixmap(crosshair)

        # Progress
        total = len(self._zones)
        marker = " *" if name in self._modified else ""
        self._progress_label.setText(f"Zone {index + 1} / {total}{marker}")

        # Zone name
        self._zone_name_label.setText(name)

        # Aliases
        aliases = self._alias_index.get(name, [])
        if aliases:
            self._aliases_label.setText("Aliases:\n" + "\n".join(f"  {a}" for a in sorted(aliases)))
        else:
            self._aliases_label.setText("Aliases: (none)")

        # Coords
        orig = self._nodes[name]["center"]
        self._coords_label.setText(
            f"Original:  ({orig[0]}, {orig[1]})\n"
            f"Current:   ({cx}, {cy})"
        )

        # Pending
        pending = self._pending[name]
        if pending:
            self._pending_label.setText(f"Pending:   ({pending[0]}, {pending[1]})\n[click Approve to commit]")
        else:
            self._pending_label.setText("")

        self._prev_btn.setEnabled(index > 0)
        self._next_btn.setEnabled(index < total - 1)
        self._status_label.setText("")

    def _on_map_click(self, mx: int, my: int):
        name = self._zones[self._index]
        self._pending[name] = [mx, my]
        # Show crosshair at pending position immediately
        crosshair = make_crosshair_pixmap(self._base_pixmap, mx, my)
        self._map_label.set_source_pixmap(crosshair)
        self._pending_label.setText(f"Pending:   ({mx}, {my})\n[click Approve to commit]")
        self._status_label.setText("")

    def _approve(self):
        name = self._zones[self._index]
        pending = self._pending[name]
        if pending:
            self._working[name] = pending
            self._pending[name] = None
            self._modified.add(name)
            self._status_label.setText(f"Saved ({pending[0]}, {pending[1]})")
        else:
            self._status_label.setText("Approved (no change)")
        self._show_zone(self._index)
        if self._index < len(self._zones) - 1:
            self._show_zone(self._index + 1)

    def _prev(self):
        if self._index > 0:
            self._show_zone(self._index - 1)

    def _next(self):
        if self._index < len(self._zones) - 1:
            self._show_zone(self._index + 1)

    def _save(self):
        for name in self._zones:
            self._data["nodes"][name]["center"] = self._working[name]
        ZONE_GRAPH_PATH.write_text(
            json.dumps(self._data, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        changed = len(self._modified)
        self._status_label.setText(f"Saved {changed} change(s) to zone_graph.json")
        self._status_label.setStyleSheet("color: green; font-size: 12px; font-weight: bold;")
        print(f"Saved. {changed} zone(s) modified: {sorted(self._modified)}")


def main():
    app = QApplication(sys.argv)
    win = ZoneValidatorWindow()
    win.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
