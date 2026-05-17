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
    preferred_window_size = (1240, 760)

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
        upper_row.addWidget(self.map_frame, 1)

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
        outer.addWidget(self.summary_stone_frame)

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
