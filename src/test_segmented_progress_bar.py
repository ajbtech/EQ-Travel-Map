import pytest
from PySide6.QtWidgets import QApplication

from ui.widgets.segmented_progress_bar import SegmentedProgressBar


def test_default_value_is_zero(qt_app):
    bar = SegmentedProgressBar()
    assert bar.value() == 0


def test_default_maximum_is_zero(qt_app):
    bar = SegmentedProgressBar()
    assert bar.maximum() == 0


def test_minimum_is_always_zero(qt_app):
    bar = SegmentedProgressBar()
    bar.setRange(10, 100)
    assert bar.minimum() == 0


def test_set_range_updates_maximum(qt_app):
    bar = SegmentedProgressBar()
    bar.setRange(0, 100)
    assert bar.maximum() == 100


def test_set_value_updates_value(qt_app):
    bar = SegmentedProgressBar()
    bar.setRange(0, 100)
    bar.setValue(60)
    assert bar.value() == 60


def test_set_value_clamps_to_maximum(qt_app):
    bar = SegmentedProgressBar()
    bar.setRange(0, 100)
    bar.setValue(150)
    assert bar.value() == 100


def test_set_value_clamps_to_zero(qt_app):
    bar = SegmentedProgressBar()
    bar.setRange(0, 100)
    bar.setValue(-5)
    assert bar.value() == 0


def test_reset_sets_value_to_zero(qt_app):
    bar = SegmentedProgressBar()
    bar.setRange(0, 100)
    bar.setValue(75)
    bar.reset()
    assert bar.value() == 0


def test_size_hint_has_positive_dimensions(qt_app):
    bar = SegmentedProgressBar()
    hint = bar.sizeHint()
    assert hint.width() > 0
    assert hint.height() > 0


def test_segment_count_is_five(qt_app):
    bar = SegmentedProgressBar()
    assert bar.segment_count == 5


def test_blue_fraction_is_zero_when_maximum_is_zero(qt_app):
    bar = SegmentedProgressBar()
    assert bar._blue_fraction() == 0.0


def test_blue_fraction_is_zero_at_value_zero(qt_app):
    bar = SegmentedProgressBar()
    bar.setRange(0, 100)
    bar.setValue(0)
    assert bar._blue_fraction() == 0.0


def test_blue_fraction_is_half_mid_first_fifth(qt_app):
    bar = SegmentedProgressBar()
    bar.setRange(0, 100)
    bar.setValue(10)  # halfway through 0-20%
    assert bar._blue_fraction() == pytest.approx(0.5)


def test_blue_fraction_wraps_in_second_fifth(qt_app):
    bar = SegmentedProgressBar()
    bar.setRange(0, 100)
    bar.setValue(30)  # halfway through 20-40% → cycle is 0.5 again
    assert bar._blue_fraction() == pytest.approx(0.5)


def test_blue_fraction_is_one_at_max(qt_app):
    bar = SegmentedProgressBar()
    bar.setRange(0, 100)
    bar.setValue(100)
    assert bar._blue_fraction() == 1.0


def test_paint_event_does_not_crash(qt_app):
    bar = SegmentedProgressBar()
    bar.resize(200, 22)
    bar.show()
    qt_app.processEvents()
    bar.setRange(0, 100)
    bar.setValue(40)
    qt_app.processEvents()
    bar.hide()
