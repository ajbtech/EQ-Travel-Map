from PySide6.QtWidgets import (
    QButtonGroup,
    QDialog,
    QDialogButtonBox,
    QHBoxLayout,
    QRadioButton,
    QSpinBox,
    QVBoxLayout,
)


class DurationDialog(QDialog):
    """Asks how long the exported video should be, in seconds."""

    _PRESETS = [
        ("30 seconds", 30),
        ("1 minute", 60),
        ("2 minutes", 120),
        ("5 minutes", 300),
    ]
    _DEFAULT_INDEX = 2

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Video length")

        layout = QVBoxLayout(self)
        self._group = QButtonGroup(self)
        for index, (label, seconds) in enumerate(self._PRESETS):
            radio = QRadioButton(label)
            radio.setProperty("seconds", seconds)
            self._group.addButton(radio, index)
            layout.addWidget(radio)
            if index == self._DEFAULT_INDEX:
                radio.setChecked(True)

        custom_row = QHBoxLayout()
        self._custom_radio = QRadioButton("Custom:")
        self._group.addButton(self._custom_radio, len(self._PRESETS))
        self._custom_spin = QSpinBox()
        self._custom_spin.setRange(10, 3600)
        self._custom_spin.setValue(120)
        self._custom_spin.setSuffix(" s")
        custom_row.addWidget(self._custom_radio)
        custom_row.addWidget(self._custom_spin)
        custom_row.addStretch(1)
        layout.addLayout(custom_row)

        buttons = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel, parent=self
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def target_seconds(self):
        checked = self._group.checkedButton()
        if checked is self._custom_radio:
            return self._custom_spin.value()
        return int(checked.property("seconds"))
