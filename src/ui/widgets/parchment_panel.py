from PySide6.QtWidgets import QFrame, QVBoxLayout


# Inset (in pixels) used when placing a ParchmentPanel inside a stone-bevel
# QFrame (input/progress views). Single source of truth so the two views
# can't drift apart again; tune here to reposition the parchment relative
# to the stone bevel.
STONE_FRAME_INSET = 9


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


def build_stone_framed_parchment(*, stone_object_name, parchment_object_name):
    """Build a stone-bevel QFrame containing a ParchmentPanel.

    Returns ``(stone_frame, parchment)``. The caller adds ``stone_frame`` to
    the view's outer layout (typically with stretch=1) and places content on
    the parchment.

    The stone frame's contents margins use ``STONE_FRAME_INSET`` on every
    side so both the input and progress views position their parchments
    identically — change the constant to reposition both at once.
    """
    stone_frame = QFrame()
    stone_frame.setObjectName(stone_object_name)
    layout = QVBoxLayout(stone_frame)
    layout.setContentsMargins(
        STONE_FRAME_INSET, STONE_FRAME_INSET, STONE_FRAME_INSET, STONE_FRAME_INSET
    )
    layout.setSpacing(0)
    parchment = ParchmentPanel()
    parchment.setObjectName(parchment_object_name)
    layout.addWidget(parchment, 1)
    return stone_frame, parchment
