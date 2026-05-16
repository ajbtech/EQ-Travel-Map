from PySide6.QtWidgets import QFrame


class ParchmentPanel(QFrame):
    """Container styled in QSS to look like a parchment riveted to the stone wall.

    The visible parchment edges (rivets, rolled corners) are drawn by a QSS
    `border-image` with `border-width: 50px`. By default Qt's layout subtracts
    that border from the widget's contents rect, so any layout placed on the
    panel only gets the inner area.

    When you want content to span the *full* widget rect (overlapping the
    decorative edges) — useful when the parchment is short and every pixel
    of vertical space matters — call `set_fill_child(widget)`. The widget is
    re-parented and resized to match the panel on every resize.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFrameShape(QFrame.NoFrame)
        self.setProperty("class", "parchmentPanel")
        self._fill_child = None

    def set_fill_child(self, widget):
        self._fill_child = widget
        widget.setParent(self)
        widget.setGeometry(self.rect())
        widget.raise_()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if self._fill_child is not None:
            self._fill_child.setGeometry(self.rect())
