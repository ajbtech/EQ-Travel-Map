from PySide6.QtCore import QSize, Qt
from PySide6.QtGui import QColor, QFont, QFontMetrics, QPainter
from PySide6.QtWidgets import QWidget


class EngravedHeading(QWidget):
    """Label-like widget that renders text as if chiseled into stone.

    The effect is three offset draws of the same string: a 1px-down, 1px-right
    light highlight, a 1px-up, 1px-left dark shadow, and the main bronze fill
    at (0, 0). Reads as engraved when sat on a textured stone background.
    """

    DEFAULT_SHADOW = QColor("#1a0e04")
    DEFAULT_HIGHLIGHT = QColor("#a98b48")
    DEFAULT_FILL = QColor("#c9a24a")

    def __init__(self, text="", parent=None):
        super().__init__(parent)
        self._text = text
        self._fill = self.DEFAULT_FILL
        self._shadow = self.DEFAULT_SHADOW
        self._highlight = self.DEFAULT_HIGHLIGHT
        font = QFont("Georgia", 22)
        font.setBold(True)
        self.setFont(font)

    def text(self):
        return self._text

    def setText(self, value):
        self._text = value
        self.updateGeometry()
        self.update()

    def sizeHint(self):
        metrics = QFontMetrics(self.font())
        rect = metrics.boundingRect(self._text or " ")
        # +2 in each axis to accommodate the offset draws.
        return QSize(rect.width() + 4, rect.height() + 4)

    def minimumSizeHint(self):
        return self.sizeHint()

    def paintEvent(self, _event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.TextAntialiasing, True)
        painter.setFont(self.font())
        rect = self.rect()
        align = Qt.AlignLeft | Qt.AlignVCenter

        painter.setPen(self._highlight)
        painter.drawText(rect.adjusted(1, 1, 1, 1), align, self._text)

        painter.setPen(self._shadow)
        painter.drawText(rect.adjusted(-1, -1, -1, -1), align, self._text)

        painter.setPen(self._fill)
        painter.drawText(rect, align, self._text)
