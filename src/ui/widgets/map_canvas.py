from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import QLabel


class MapCanvas(QLabel):
    """Displays the rendered map PNG, scaled to fit the current widget size.

    The map renderer (`eq_parser.draw_zone_path`) writes a PNG to disk; this
    widget loads that PNG and keeps the image rescaled on resize so the map
    always fills the parchment panel without distortion.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self._source_pixmap = None
        self.setObjectName("mapCanvas")
        self.setAlignment(Qt.AlignCenter)
        self.setMinimumSize(400, 250)
        self.setText("(no map loaded)")

    def load_image(self, image_path):
        path = Path(image_path)
        if not path.exists():
            self._source_pixmap = None
            self.setText(f"Map image not found: {path.name}")
            return
        pixmap = QPixmap(str(path))
        if pixmap.isNull():
            self._source_pixmap = None
            self.setText(f"Could not load map image: {path.name}")
            return
        self._source_pixmap = pixmap
        self._refresh_scaled()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._refresh_scaled()

    def _refresh_scaled(self):
        if self._source_pixmap is None:
            return
        scaled = self._source_pixmap.scaled(
            self.size(),
            Qt.KeepAspectRatio,
            Qt.SmoothTransformation,
        )
        self.setPixmap(scaled)
