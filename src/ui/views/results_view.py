import shutil
from html import escape
from pathlib import Path

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QGuiApplication
from PySide6.QtWidgets import (
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from ui.widgets.map_canvas import MapCanvas
from ui.widgets.parchment_panel import ParchmentPanel


class ResultsView(QWidget):
    back_requested = Signal()
    # Target window height. The width is computed from this height in
    # `preferred_window_size` so the window hugs the rendered map + button
    # column with no blank space on the right.
    _PREFERRED_HEIGHT = 700
    # Vertical space the summary stone+parchment takes up: 18px stone bevel
    # + 37px parchment border-image + 95px content + 37px border-image + 18px
    # stone bevel. Drift here if the QSS border-widths change.
    _SUMMARY_TOTAL_HEIGHT = 205
    # Total width of the button column (buttons are setFixedWidth(200), plus
    # the 18px stone bevel on each side).
    _BUTTON_FRAME_WIDTH = 236
    # Matches QFrame#mapFrame border-width in the QSS theme; the bevel paints
    # an 18px stone border on each side of the contained MapCanvas.
    _MAP_FRAME_BORDER = 18
    # Aspect ratio of zone_map.png (2700x1550). Used as a fallback when the
    # rendered map hasn't been loaded yet (e.g. during view construction).
    _FALLBACK_MAP_ASPECT = 2700 / 1550

    @property
    def preferred_window_size(self):
        aspect = self.map_canvas.source_aspect_ratio() or self._FALLBACK_MAP_ASPECT
        border = self._MAP_FRAME_BORDER
        inner_h = self._PREFERRED_HEIGHT - self._SUMMARY_TOTAL_HEIGHT - 2 * border
        map_w = int(round(inner_h * aspect)) + 2 * border
        return (map_w + self._BUTTON_FRAME_WIDTH, self._PREFERRED_HEIGHT)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("resultsView")
        self._current_image_path = None
        self._current_sections = None

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        upper_row = QHBoxLayout()
        upper_row.setContentsMargins(0, 0, 0, 0)
        upper_row.setSpacing(0)

        self.map_frame = QFrame()
        self.map_frame.setObjectName("mapFrame")
        map_frame_layout = QVBoxLayout(self.map_frame)
        map_frame_layout.setContentsMargins(0, 0, 0, 0)
        self.map_canvas = MapCanvas()
        map_frame_layout.addWidget(self.map_canvas)
        # No stretch on the map frame: its width is driven by
        # _fit_map_frame_to_image() so the stone bevel hugs the rendered
        # map. Trailing stretch (added after the button column) absorbs any
        # leftover horizontal space.
        upper_row.addWidget(self.map_frame)

        self.button_frame = QFrame()
        self.button_frame.setObjectName("buttonFrame")
        button_column = QVBoxLayout(self.button_frame)
        button_column.setContentsMargins(0, 0, 0, 0)
        button_column.setSpacing(8)

        self.back_button = QPushButton("NEW INPUT")
        self.back_button.setObjectName("bronzeButton")
        self.back_button.setFixedWidth(200)
        self.back_button.clicked.connect(self.back_requested.emit)
        button_column.addWidget(self.back_button)

        self.copy_text_button = QPushButton("COPY TEXT")
        self.copy_text_button.setObjectName("bronzeButton")
        self.copy_text_button.setFixedWidth(200)
        self.copy_text_button.clicked.connect(self._on_copy_text)
        button_column.addWidget(self.copy_text_button)

        self.save_image_button = QPushButton("SAVE MAP")
        self.save_image_button.setObjectName("bronzeButton")
        self.save_image_button.setFixedWidth(200)
        self.save_image_button.clicked.connect(self._on_save_image)
        button_column.addWidget(self.save_image_button)

        button_column.addStretch(1)
        upper_row.addWidget(self.button_frame)
        upper_row.addStretch(1)

        outer.addLayout(upper_row, 1)

        self.summary_stone_frame = QFrame()
        self.summary_stone_frame.setObjectName("summaryStoneFrame")
        summary_stone_layout = QVBoxLayout(self.summary_stone_frame)
        summary_stone_layout.setContentsMargins(0, 0, 0, 0)
        summary_stone_layout.setSpacing(0)

        summary_parchment = ParchmentPanel()
        summary_parchment.setObjectName("summaryParchment")

        # The columns live in an overlay widget that fills the entire
        # parchment rect (set_fill_child), so text can use the full widget
        # area instead of being squeezed inside the 50px border-image.
        columns_container = QWidget()
        columns_container.setAttribute(Qt.WA_TranslucentBackground)
        columns_layout = QHBoxLayout(columns_container)
        columns_layout.setContentsMargins(40, 18, 20, 4)
        columns_layout.setSpacing(12)

        self._kills_column = self._make_column()
        self._zones_column = self._make_column()
        self._stats_column = self._make_column()

        columns_layout.addWidget(self._kills_column, 1, Qt.AlignTop)
        columns_layout.addWidget(self._zones_column, 1, Qt.AlignTop)
        columns_layout.addWidget(self._stats_column, 2, Qt.AlignTop)

        summary_parchment.set_fill_child(columns_container)
        summary_stone_layout.addWidget(summary_parchment)

        # Wrap the summary in an HBox with a trailing stretch so it can be
        # sized to match the upper row's content width (map_frame +
        # button_frame) rather than spanning the full window. The stretch
        # absorbs any leftover space on the right.
        summary_row = QHBoxLayout()
        summary_row.setContentsMargins(0, 0, 0, 0)
        summary_row.setSpacing(0)
        summary_row.addWidget(self.summary_stone_frame)
        summary_row.addStretch(1)
        outer.addLayout(summary_row)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._fit_map_frame_to_image()

    def _fit_map_frame_to_image(self):
        aspect = self.map_canvas.source_aspect_ratio()
        if aspect is None:
            return
        border = self._MAP_FRAME_BORDER
        inner_h = self.map_frame.height() - 2 * border
        if inner_h <= 0:
            return
        target = int(round(inner_h * aspect)) + 2 * border
        if (
            self.map_frame.minimumWidth() != target
            or self.map_frame.maximumWidth() != target
        ):
            self.map_frame.setFixedWidth(target)
        self._fit_summary_to_upper_row()

    def _fit_summary_to_upper_row(self):
        # Span the summary parchment under the map AND the button column so
        # the stone bevels line up on the right.
        summary_w = self.map_frame.width() + self.button_frame.sizeHint().width()
        if (
            self.summary_stone_frame.minimumWidth() != summary_w
            or self.summary_stone_frame.maximumWidth() != summary_w
        ):
            self.summary_stone_frame.setFixedWidth(summary_w)

    def _make_column(self):
        label = QLabel("")
        label.setObjectName("summaryColumn")
        label.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        label.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Maximum)
        return label

    def set_results(self, image_path, summary_sections):
        self._current_image_path = Path(image_path)
        self._current_sections = summary_sections
        self.map_canvas.load_image(self._current_image_path)
        self._fit_map_frame_to_image()
        self._kills_column.setText(
            self._render_column_html(summary_sections.top_kills_lines)
        )
        self._zones_column.setText(
            self._render_column_html(summary_sections.top_zones_lines)
        )
        self._stats_column.setText(
            self._render_column_html(
                ["Major Statistics", *summary_sections.stats_lines],
            )
        )

    @staticmethod
    def _render_column_html(lines):
        if not lines:
            return ""
        head = f"<b><u>{escape(lines[0])}</u></b>"
        body = [escape(line) for line in lines[1:]]
        return "<br>".join([head, *body])

    def summary_text(self):
        if self._current_sections is None:
            return ""
        parts = []
        if self._current_sections.character_line:
            parts.append(self._current_sections.character_line)
            parts.append("")
        parts.extend(self._current_sections.top_kills_lines)
        parts.append("")
        parts.extend(self._current_sections.top_zones_lines)
        parts.append("")
        parts.extend(self._current_sections.stats_lines)
        return "\n".join(parts)

    def _on_copy_text(self):
        QGuiApplication.clipboard().setText(self.summary_text())

    def _on_save_image(self):
        if self._current_image_path is None or not self._current_image_path.exists():
            return
        suggested = str(Path.home() / self._suggested_save_filename())
        chosen, _filter = QFileDialog.getSaveFileName(
            self,
            "Save map as",
            suggested,
            "PNG image (*.png);;All files (*)",
        )
        if not chosen:
            return
        shutil.copyfile(self._current_image_path, chosen)

    def _suggested_save_filename(self):
        original = self._current_image_path.name
        character = self._character_name()
        if not character:
            return original
        return f"{character}_{original}"

    def _character_name(self):
        if self._current_sections is None:
            return ""
        line = self._current_sections.character_line
        prefix = "Character: "
        if line.startswith(prefix):
            return line[len(prefix) :].strip()
        return ""
