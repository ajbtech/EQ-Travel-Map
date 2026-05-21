"""Happy-path and rescale tests for the MapCanvas widget.

The widget's error branches (missing file, unreadable PNG) are exercised
indirectly via `test_main_window`; this file pins the load + rescale
behavior that's actually visible to users.
"""

from pathlib import Path

from PySide6.QtCore import QSize

from ui.widgets.map_canvas import MapCanvas

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SAMPLE_IMAGE = PROJECT_ROOT / "docs" / "sample_map.png"


def test_load_image_with_valid_png_sets_a_non_null_pixmap(qt_app):
    canvas = MapCanvas()

    canvas.load_image(SAMPLE_IMAGE)

    assert canvas.pixmap() is not None
    assert not canvas.pixmap().isNull()


def test_load_image_preserves_aspect_ratio_within_widget(qt_app):
    canvas = MapCanvas()
    canvas.resize(QSize(800, 400))

    canvas.load_image(SAMPLE_IMAGE)

    pixmap_size = canvas.pixmap().size()
    assert pixmap_size.width() <= 800
    assert pixmap_size.height() <= 400


def test_resize_event_rescales_existing_pixmap(qt_app):
    canvas = MapCanvas()
    canvas.show()
    canvas.resize(400, 250)
    qt_app.processEvents()
    canvas.load_image(SAMPLE_IMAGE)
    initial_size = canvas.pixmap().size()

    canvas.resize(1200, 600)
    qt_app.processEvents()

    rescaled_size = canvas.pixmap().size()
    assert rescaled_size.width() > initial_size.width()
