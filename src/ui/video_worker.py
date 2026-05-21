"""Drives video frame capture on the main Qt thread.

A ``VideoGenerator`` yields per-frame data; for each frame this worker pushes the
map + columns into an offscreen ``ResultsView``, captures it with
``QWidget.render`` and appends the pixels to an MP4 via imageio. Frames are
scheduled one at a time with ``QTimer.singleShot(0, ...)`` so the Qt event loop
keeps spinning and the progress dialog (and its Cancel button) stay responsive.
"""

from pathlib import Path

import imageio.v2 as imageio
import numpy as np
from PySide6.QtCore import QObject, Qt, QTimer, Signal
from PySide6.QtGui import QImage, QPixmap


def pil_to_qpixmap(pil_image):
    rgb = pil_image.convert("RGB")
    data = np.ascontiguousarray(np.asarray(rgb))
    height, width, _ = data.shape
    qimage = QImage(data.tobytes(), width, height, width * 3, QImage.Format_RGB888)
    return QPixmap.fromImage(qimage.copy())


def qimage_to_numpy(qimage):
    qimage = qimage.convertToFormat(QImage.Format_RGB888)
    width = qimage.width()
    height = qimage.height()
    bytes_per_line = qimage.bytesPerLine()
    buffer = bytes(qimage.constBits())[: bytes_per_line * height]
    # QImage rows are 4-byte aligned, so width*3 may be padded; slice it off.
    rows = np.frombuffer(buffer, np.uint8).reshape(height, bytes_per_line)
    return rows[:, : width * 3].reshape(height, width, 3).copy()


class VideoWorker(QObject):
    progress = Signal(int, int)
    finished = Signal(str)
    error = Signal(str)
    canceled = Signal()

    def __init__(self, generator, offscreen_view, output_path, fps=24):
        super().__init__()
        self._generator = generator
        self._view = offscreen_view
        self._output_path = Path(output_path)
        self._fps = fps
        self._writer = None
        self._frame_iter = None
        self._cancel_requested = False
        self._last_content_version = -1
        self._last_numpy_frame = None
        self._pixmap_loaded = False

    def start(self):
        try:
            self._writer = imageio.get_writer(
                str(self._output_path),
                fps=self._fps,
                codec="libx264",
                quality=8,
                # imageio defaults the output pixel format to yuv420p (broad
                # player support); that requires even frame dimensions, which
                # the caller guarantees. macro_block_size=None avoids silent
                # resizing if a dimension still isn't a multiple of 16.
                macro_block_size=None,
            )
            self._frame_iter = self._generator.frames()
        except Exception as exc:
            self._cleanup(delete_output=True)
            self.error.emit(str(exc))
            return
        QTimer.singleShot(0, self._process_next_frame)

    def cancel(self):
        self._cancel_requested = True

    def _process_next_frame(self):
        if self._cancel_requested:
            self._cleanup(delete_output=True)
            self.canceled.emit()
            return

        try:
            frame = next(self._frame_iter)
        except StopIteration:
            # Closing the writer is where ffmpeg finalizes (and writes) the file,
            # so a failure here (e.g. ffmpeg died mid-stream) means the export did
            # NOT succeed. Surface it as an error instead of a false "finished".
            try:
                self._finalize_writer()
            except Exception as exc:
                self._cleanup(delete_output=True)
                self.error.emit(str(exc))
                return
            self._cleanup()
            self.finished.emit(str(self._output_path))
            return
        except Exception as exc:
            self._cleanup(delete_output=True)
            self.error.emit(str(exc))
            return

        try:
            if frame.content_version != self._last_content_version:
                if frame.map_updated or not self._pixmap_loaded:
                    self._view.map_canvas.load_pixmap(pil_to_qpixmap(frame.map_image))
                    self._pixmap_loaded = True
                self._view.set_columns(
                    frame.top_kills_lines, frame.top_zones_lines, frame.stats_lines
                )
                self._view.level_heading.setText(frame.level_line)
                image = QImage(self._view.size(), QImage.Format_RGB888)
                image.fill(Qt.black)
                self._view.render(image)
                self._last_numpy_frame = qimage_to_numpy(image)
                self._last_content_version = frame.content_version
            self._writer.append_data(self._last_numpy_frame)
        except Exception as exc:
            self._cleanup(delete_output=True)
            self.error.emit(str(exc))
            return

        self.progress.emit(frame.frame_index + 1, frame.total_frames)
        QTimer.singleShot(0, self._process_next_frame)

    def _finalize_writer(self):
        if self._writer is not None:
            writer = self._writer
            self._writer = None
            writer.close()

    def _cleanup(self, delete_output=False):
        if self._writer is not None:
            try:
                self._writer.close()
            except Exception:
                pass
            self._writer = None
        if delete_output and self._output_path.exists():
            try:
                self._output_path.unlink()
            except OSError:
                pass
