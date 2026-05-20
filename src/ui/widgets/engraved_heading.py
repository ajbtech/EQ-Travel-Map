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
    _MIN_POINT_SIZE = 10

    def __init__(self, text="", parent=None):
        super().__init__(parent)
        self._text = text
        self._fill = self.DEFAULT_FILL
        self._shadow = self.DEFAULT_SHADOW
        self._highlight = self.DEFAULT_HIGHLIGHT
        self._engraved = True
        self._alignment = Qt.AlignLeft | Qt.AlignVCenter
        font = QFont("Georgia", 22)
        font.setBold(True)
        self.setFont(font)

    def set_color(self, fill):
        self._fill = QColor(fill)
        self.update()

    def setAlignment(self, alignment):
        self._alignment = alignment
        self.update()

    def set_engraved(self, enabled):
        """Toggle the chiseled offset draws; when off the text renders flat."""
        self._engraved = bool(enabled)
        self.update()

    def text(self):
        return self._text

    def setText(self, value):
        self._text = value
        self.updateGeometry()
        self.update()

    def _effective_font(self):
        """Base font shrunk just enough that the text fits the widget width.

        The heading lives in a fixed-width column, so long character names
        would otherwise be clipped. Shrink the point size (down to a floor)
        until the string fits the available width.
        """
        font = QFont(self.font())
        available = self.width() - 4  # leave room for the offset draws
        if available <= 0 or not self._text:
            return font
        size = font.pointSize()
        while size > self._MIN_POINT_SIZE:
            if QFontMetrics(font).horizontalAdvance(self._text) <= available:
                break
            size -= 1
            font.setPointSize(size)
        return font

    def sizeHint(self):
        metrics = QFontMetrics(self.font())
        rect = metrics.boundingRect(self._text or " ")
        # +2 in each axis to accommodate the offset draws.
        return QSize(rect.width() + 4, rect.height() + 4)

    def minimumSizeHint(self):
        metrics = QFontMetrics(self.font())
        return QSize(0, metrics.height() + 4)

    def paintEvent(self, _event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.TextAntialiasing, True)
        painter.setFont(self._effective_font())
        rect = self.rect()
        align = self._alignment

        if self._engraved:
            painter.setPen(self._highlight)
            painter.drawText(rect.adjusted(1, 1, 1, 1), align, self._text)

            painter.setPen(self._shadow)
            painter.drawText(rect.adjusted(-1, -1, -1, -1), align, self._text)

        painter.setPen(self._fill)
        painter.drawText(rect, align, self._text)
