from pathlib import Path

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QFileDialog,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from ui.widgets.parchment_panel import build_stone_framed_parchment


class InputView(QWidget):
    parse_requested = Signal(str, str, str)
    preferred_window_size = (720, 360)

    def __init__(
        self,
        default_log_folder,
        default_output_path,
        default_character_name="",
        parent=None,
    ):
        super().__init__(parent)
        self._default_output_path = Path(default_output_path)
        self.setObjectName("inputView")

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        stone_frame, parchment = build_stone_framed_parchment(
            stone_object_name="inputStoneFrame",
            parchment_object_name="inputParchment",
        )
        outer.addWidget(stone_frame, 1)

        body = QVBoxLayout(parchment)
        body.setContentsMargins(16, 4, 16, 16)
        body.setSpacing(10)

        title = QLabel("EverQuest Travel Map")
        title.setObjectName("parchmentTitle")
        title.setAlignment(Qt.AlignHCenter)
        body.addWidget(title)

        form = QGridLayout()
        form.setHorizontalSpacing(10)
        form.setVerticalSpacing(8)
        form.setColumnStretch(1, 1)
        body.addLayout(form)

        char_label = QLabel("Character")
        char_label.setObjectName("formLabel")
        self.character_input = QLineEdit(default_character_name)
        self.character_input.setObjectName("formInput")
        self.character_input.setMinimumWidth(220)
        self.character_input.setToolTip(
            "Your character's name as it appears in the log filename "
            "(eqlog_<Character>_*.txt)."
        )
        self.character_input.setPlaceholderText("e.g. Gorrek")

        folder_label = QLabel("Log folder")
        folder_label.setObjectName("formLabel")
        self.folder_input = QLineEdit(str(default_log_folder))
        self.folder_input.setObjectName("formInput")
        self.folder_input.setMinimumWidth(280)
        self.folder_input.setToolTip("The folder containing your EverQuest log files.")

        self.browse_button = QPushButton("BROWSE")
        self.browse_button.setObjectName("bronzeButton")
        self.browse_button.clicked.connect(self._on_browse_clicked)

        form.addWidget(char_label, 0, 0)
        form.addWidget(self.character_input, 0, 1, 1, 2)
        form.addWidget(folder_label, 1, 0)
        form.addWidget(self.folder_input, 1, 1)
        form.addWidget(self.browse_button, 1, 2)

        self.error_label = QLabel("")
        self.error_label.setObjectName("formError")
        self.error_label.setWordWrap(True)
        self.error_label.setVisible(False)
        body.addWidget(self.error_label)

        body.addStretch(1)

        button_row = QHBoxLayout()
        button_row.addStretch(1)
        self.generate_button = QPushButton("GENERATE")
        self.generate_button.setObjectName("bronzeButton")
        self.generate_button.setMinimumWidth(150)
        self.generate_button.clicked.connect(self._on_generate_clicked)
        button_row.addWidget(self.generate_button)
        body.addLayout(button_row)

        self.character_input.textChanged.connect(self._on_input_changed)
        self.folder_input.textChanged.connect(self._on_input_changed)
        self._refresh_generate_state()

    def _on_browse_clicked(self):
        current = self.folder_input.text() or str(Path.home())
        chosen = QFileDialog.getExistingDirectory(self, "Choose log folder", current)
        if chosen:
            self.folder_input.setText(chosen)

    def _on_input_changed(self, _text):
        if self.error_label.isVisible():
            self.error_label.setVisible(False)
        self._refresh_generate_state()

    def _refresh_generate_state(self):
        character = self.character_input.text().strip()
        folder = self.folder_input.text().strip()
        self.generate_button.setEnabled(bool(character) and bool(folder))

    def _validation_error(self, character, folder):
        if not character and not folder:
            return "Enter a character name and choose a log folder."
        if not character:
            return "Enter a character name."
        if not folder:
            return "Choose a log folder."
        if not Path(folder).is_dir():
            return f"Log folder does not exist: {folder}"
        if not any(Path(folder).glob(f"*eqlog_{character}_*.txt")):
            return f'No log files found for "{character}" in this folder.'
        return ""

    def _on_generate_clicked(self):
        character = self.character_input.text().strip()
        folder = self.folder_input.text().strip()
        error = self._validation_error(character, folder)
        if error:
            self.error_label.setText(error)
            self.error_label.setVisible(True)
            return
        self.error_label.setVisible(False)
        self.parse_requested.emit(character, folder, str(self._default_output_path))
