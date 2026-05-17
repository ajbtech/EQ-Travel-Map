from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QProgressBar,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from ui.widgets.parchment_panel import build_stone_framed_parchment


def _format_count(value):
    return f"{value:,}"


class ProgressView(QWidget):
    cancel_requested = Signal()
    preferred_window_size = (720, 360)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("progressView")

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        stone_frame, parchment = build_stone_framed_parchment(
            stone_object_name="progressStoneFrame",
            parchment_object_name="progressParchment",
        )
        outer.addWidget(stone_frame, 1)

        body = QVBoxLayout(parchment)
        body.setContentsMargins(28, 4, 28, 20)
        body.setSpacing(12)

        title = QLabel("EverQuest Travel Map")
        title.setObjectName("parchmentTitle")
        title.setAlignment(Qt.AlignHCenter)
        body.addWidget(title)

        self.character_label = QLabel("")
        self.character_label.setObjectName("progressCharacter")
        body.addWidget(self.character_label)

        self.file_label = QLabel("Current file: —")
        self.file_label.setObjectName("progressDetail")
        body.addWidget(self.file_label)

        self.lines_label = QLabel("Lines parsed: 0")
        self.lines_label.setObjectName("progressDetail")
        body.addWidget(self.lines_label)

        self.progress_bar = QProgressBar()
        self.progress_bar.setObjectName("stoneProgress")
        self.progress_bar.setRange(0, 0)
        body.addWidget(self.progress_bar)

        body.addStretch(1)

        button_row = QHBoxLayout()
        button_row.addStretch(1)
        self.cancel_button = QPushButton("CANCEL")
        self.cancel_button.setObjectName("bronzeButton")
        self.cancel_button.setMinimumWidth(150)
        self.cancel_button.clicked.connect(self.cancel_requested.emit)
        button_row.addWidget(self.cancel_button)
        body.addLayout(button_row)

    def set_character(self, character_name):
        self.character_label.setText(f"Parsing logs for {character_name}...")

    def set_progress(self, file_name, line_count):
        self.file_label.setText(f"Current file: {file_name}")
        self.lines_label.setText(f"Lines parsed: {_format_count(line_count)}")
