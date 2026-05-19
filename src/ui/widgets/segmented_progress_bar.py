from PySide6.QtCore import QRectF, QSize, Qt
from PySide6.QtGui import QColor, QLinearGradient, QPainter, QPainterPath
from PySide6.QtWidgets import QSizePolicy, QWidget


class SegmentedProgressBar(QWidget):
    """Five-segment bone-style progress bar matching the EQ aesthetic.

    Segments fill left-to-right from grey (empty) to gold (filled).
    Dark gear end-caps frame each side. API is a compatible subset of
    QProgressBar: setRange / setValue / value / maximum / minimum / reset.
    """

    segment_count = 5

    # Gold (filled) gradient stops: top → mid → bottom
    _GOLD_TOP = QColor("#fff0a8")
    _GOLD_MID = QColor("#f5c542")
    _GOLD_BOT = QColor("#a87a1a")

    # Grey (empty) gradient stops
    _GREY_TOP = QColor("#c8c0b0")
    _GREY_MID = QColor("#8a8070")
    _GREY_BOT = QColor("#504840")

    # Blue sub-indicator gradient stops
    _BLUE_TOP = QColor("#a8d4ff")
    _BLUE_MID = QColor("#3a7fd4")
    _BLUE_BOT = QColor("#1a3f6f")

    # Structural colours
    _BG = QColor("#1a1208")
    _CAP_DARK = QColor("#1a0e04")
    _CAP_RING = QColor("#6c6358")
    _SEG_BORDER = QColor("#0d0905")
    _SHEEN = QColor(255, 255, 255, 55)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._minimum = 0
        self._maximum = 0
        self._value = 0
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def minimum(self):
        return 0

    def maximum(self):
        return self._maximum

    def value(self):
        return self._value

    def setRange(self, minimum, maximum):  # noqa: N802
        self._minimum = 0
        self._maximum = max(0, maximum)
        self._value = min(self._value, self._maximum)
        self.update()

    def setValue(self, value):  # noqa: N802
        self._value = max(0, min(value, self._maximum))
        self.update()

    def reset(self):
        self._value = 0
        self.update()

    # ------------------------------------------------------------------
    # Qt overrides
    # ------------------------------------------------------------------

    def sizeHint(self):
        return QSize(200, 22)

    def minimumSizeHint(self):
        return QSize(100, 18)

    def paintEvent(self, _event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        w = self.width()
        h = self.height()

        # Background
        painter.fillRect(self.rect(), self._BG)

        cap_r = h / 2.0
        bar_left = cap_r
        bar_right = w - cap_r
        bar_w = bar_right - bar_left

        n = self.segment_count
        gap = max(2, int(h * 0.12))
        seg_w = (bar_w - gap * (n - 1)) / n

        # How many segments are fully filled?
        filled_frac = self._value / self._maximum if self._maximum > 0 else 0.0
        filled_float = filled_frac * n  # e.g. 2.4 → 2 full, 1 partial

        for i in range(n):
            x = bar_left + i * (seg_w + gap)
            seg_fill = max(0.0, min(1.0, filled_float - i))
            self._draw_segment(painter, x, 0, seg_w, h, seg_fill)

        self._draw_sub_indicator(painter, bar_left, bar_right, h)

        self._draw_cap(painter, 0, h)
        self._draw_cap(painter, w, h)

    def _blue_fraction(self):
        """Blue line's fill ratio: cycles 0→1 once per fifth of yellow progress."""
        if self._maximum <= 0:
            return 0.0
        yellow_frac = self._value / self._maximum
        if yellow_frac >= 1.0:
            return 1.0
        return (yellow_frac * self.segment_count) % 1.0

    def _draw_sub_indicator(self, painter, x_start, x_end, h):
        blue_frac = self._blue_fraction()
        if blue_frac <= 0:
            return

        bar_w = x_end - x_start
        line_h = max(2.0, h * 0.12)
        line_y = (h - line_h) / 2.0
        fill_w = bar_w * blue_frac

        grad = QLinearGradient(x_start, line_y, x_start, line_y + line_h)
        grad.setColorAt(0.0, self._BLUE_TOP)
        grad.setColorAt(0.5, self._BLUE_MID)
        grad.setColorAt(1.0, self._BLUE_BOT)
        painter.fillRect(QRectF(x_start, line_y, fill_w, line_h), grad)

    # ------------------------------------------------------------------
    # Drawing helpers
    # ------------------------------------------------------------------

    def _draw_segment(self, painter, x, y, w, h, fill_fraction):
        radius = h * 0.28

        # Dark outer border
        border_path = self._rounded_rect(x, y + 1, w, h - 2, radius)
        painter.fillPath(border_path, self._SEG_BORDER)

        inner_x = x + 1
        inner_y = y + 2
        inner_w = w - 2
        inner_h = h - 4

        if fill_fraction <= 0.0:
            self._fill_gradient(
                painter,
                inner_x,
                inner_y,
                inner_w,
                inner_h,
                radius * 0.7,
                self._GREY_TOP,
                self._GREY_MID,
                self._GREY_BOT,
            )
        elif fill_fraction >= 1.0:
            self._fill_gradient(
                painter,
                inner_x,
                inner_y,
                inner_w,
                inner_h,
                radius * 0.7,
                self._GOLD_TOP,
                self._GOLD_MID,
                self._GOLD_BOT,
            )
        else:
            # Split: gold on left, grey on right
            split_x = inner_x + inner_w * fill_fraction
            gold_w = split_x - inner_x
            grey_w = inner_w - gold_w

            gold_clip = self._rounded_rect(
                inner_x, inner_y, gold_w, inner_h, radius * 0.7
            )
            grey_clip = self._rounded_rect(
                split_x, inner_y, grey_w, inner_h, radius * 0.7
            )

            if gold_w > 0:
                self._fill_gradient(
                    painter,
                    inner_x,
                    inner_y,
                    inner_w,
                    inner_h,
                    radius * 0.7,
                    self._GOLD_TOP,
                    self._GOLD_MID,
                    self._GOLD_BOT,
                    clip_path=gold_clip,
                )
            if grey_w > 0:
                self._fill_gradient(
                    painter,
                    inner_x,
                    inner_y,
                    inner_w,
                    inner_h,
                    radius * 0.7,
                    self._GREY_TOP,
                    self._GREY_MID,
                    self._GREY_BOT,
                    clip_path=grey_clip,
                )

        # Top sheen stripe
        sheen_path = self._rounded_rect(
            inner_x, inner_y, inner_w, inner_h * 0.4, radius * 0.7
        )
        painter.fillPath(sheen_path, self._SHEEN)

    def _fill_gradient(
        self, painter, x, y, w, h, radius, top, mid, bot, clip_path=None
    ):
        grad = QLinearGradient(x, y, x, y + h)
        grad.setColorAt(0.0, top)
        grad.setColorAt(0.5, mid)
        grad.setColorAt(1.0, bot)

        path = (
            clip_path
            if clip_path is not None
            else self._rounded_rect(x, y, w, h, radius)
        )
        painter.fillPath(path, grad)

    def _draw_cap(self, painter, center_x, h):
        r = h / 2.0
        cx = center_x
        cy = h / 2.0

        # Dark filled circle
        cap_path = QPainterPath()
        cap_path.addEllipse(cx - r, cy - r, r * 2, r * 2)
        painter.fillPath(cap_path, self._CAP_DARK)

        # Ring stroke
        painter.setPen(self._CAP_RING)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawEllipse(
            int(cx - r + 1), int(cy - r + 1), int(r * 2 - 2), int(r * 2 - 2)
        )

        # Spokes
        import math

        spoke_inner = r * 0.45
        spoke_outer = r * 0.88
        spoke_count = 8
        painter.setPen(self._CAP_RING)
        for k in range(spoke_count):
            angle = math.radians(k * 360 / spoke_count)
            x1 = cx + spoke_inner * math.cos(angle)
            y1 = cy + spoke_inner * math.sin(angle)
            x2 = cx + spoke_outer * math.cos(angle)
            y2 = cy + spoke_outer * math.sin(angle)
            painter.drawLine(int(x1), int(y1), int(x2), int(y2))

        # Centre dot
        dot_r = r * 0.18
        dot_path = QPainterPath()
        dot_path.addEllipse(cx - dot_r, cy - dot_r, dot_r * 2, dot_r * 2)
        painter.fillPath(dot_path, self._CAP_RING)

    @staticmethod
    def _rounded_rect(x, y, w, h, radius):
        path = QPainterPath()
        path.addRoundedRect(x, y, w, h, radius, radius)
        return path
