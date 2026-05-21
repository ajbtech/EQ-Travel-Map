from PySide6.QtGui import QColor, QFontMetrics

from ui.widgets.engraved_heading import EngravedHeading


def test_set_color_changes_fill(qt_app):
    heading = EngravedHeading("Gorrek")
    heading.set_color(QColor("black"))
    assert heading._fill == QColor("black")


def test_long_name_shrinks_to_fit_width(qt_app):
    heading = EngravedHeading()
    heading.setFixedWidth(200)
    heading.setText("Gorrekthegreat")
    font = heading._effective_font()
    advance = QFontMetrics(font).horizontalAdvance(heading.text())
    assert advance <= heading.width()


def test_short_name_keeps_base_point_size(qt_app):
    heading = EngravedHeading()
    heading.setFixedWidth(200)
    base = heading.font().pointSize()
    heading.setText("Bob")
    assert heading._effective_font().pointSize() == base


def test_set_engraved_toggles_flag(qt_app):
    heading = EngravedHeading()
    assert heading._engraved is True
    heading.set_engraved(False)
    assert heading._engraved is False
