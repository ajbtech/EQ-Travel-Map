from html import escape

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QLabel,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)


class MoreStatsDialog(QDialog):
    def __init__(self, sections, parent=None):
        super().__init__(parent)
        self.setWindowTitle("More Statistics")
        self.setModal(False)
        self.resize(480, 600)

        scroll = QScrollArea(self)
        scroll.setWidgetResizable(True)

        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(16, 16, 16, 16)
        content_layout.setSpacing(16)

        for section_lines in [
            sections.extended_zones_lines,
            sections.extended_kills_lines,
            sections.extended_spells_lines,
            sections.max_damage_lines,
        ]:
            label = QLabel(self._render_html(section_lines))
            label.setWordWrap(True)
            label.setTextInteractionFlags(Qt.TextSelectableByMouse)
            label.setAlignment(Qt.AlignTop | Qt.AlignLeft)
            content_layout.addWidget(label)

        content_layout.addStretch(1)
        scroll.setWidget(content)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(scroll)

    @staticmethod
    def _render_html(lines):
        if not lines:
            return ""
        head = f"<b>{escape(lines[0])}</b>"
        body = "<br>".join(escape(line) for line in lines[1:])
        return f"{head}<br>{body}"
