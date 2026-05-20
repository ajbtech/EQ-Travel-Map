from pathlib import Path

import numpy as np
import pytest
from PIL import Image
from PySide6.QtCore import QEventLoop, Qt

import log_parser
import summary_formatter
import video_generator
from ui.video_worker import VideoWorker, pil_to_qpixmap, qimage_to_numpy

_SAMPLE_MAP = Path(__file__).resolve().parents[1] / "docs" / "sample_map.png"


def _ffmpeg_available():
    try:
        import imageio_ffmpeg

        imageio_ffmpeg.get_ffmpeg_exe()
        return True
    except Exception:
        return False


def test_pil_to_qpixmap_preserves_size(qt_app):
    image = Image.new("RGB", (8, 6), (10, 20, 30))
    pixmap = pil_to_qpixmap(image)
    assert (pixmap.width(), pixmap.height()) == (8, 6)


def test_qimage_to_numpy_round_trips_pixels(qt_app):
    image = Image.new("RGB", (5, 3), (200, 100, 50))
    pixmap = pil_to_qpixmap(image)
    arr = qimage_to_numpy(pixmap.toImage())
    assert arr.shape == (3, 5, 3)
    assert np.all(arr == np.array([200, 100, 50], dtype=np.uint8))


@pytest.mark.skipif(not _ffmpeg_available(), reason="ffmpeg not available")
def test_worker_writes_mp4_with_expected_frame_count(qt_app, tmp_path):
    from ui.views.results_view import ResultsView

    lines = [f"[ts] You have slain mob{i}!" for i in range(6)]
    kill_list, zone_list, summary = log_parser.parse_log_lines(lines)
    sections = summary_formatter.build_summary_sections(
        kill_list, zone_list, summary, "Gorrek"
    )

    offscreen = ResultsView()
    offscreen.setAttribute(Qt.WA_DontShowOnScreen, True)
    offscreen.setFixedSize(320, 240)
    offscreen.set_results(_SAMPLE_MAP, sections)
    offscreen.show()

    gen = video_generator.VideoGenerator(
        "Gorrek", zone_list, summary, target_seconds=1, fps=6
    )
    output = tmp_path / "out.mp4"
    worker = VideoWorker(gen, offscreen, output, fps=6)

    result = {}
    loop = QEventLoop()
    worker.finished.connect(lambda p: (result.__setitem__("ok", p), loop.quit()))
    worker.error.connect(lambda m: (result.__setitem__("err", m), loop.quit()))
    worker.start()
    loop.exec()

    assert "err" not in result, result.get("err")
    assert output.exists() and output.stat().st_size > 0

    import imageio.v2 as imageio

    reader = imageio.get_reader(str(output))
    assert sum(1 for _ in reader) == gen.total_frames()


@pytest.mark.skipif(not _ffmpeg_available(), reason="ffmpeg not available")
def test_worker_cancel_removes_partial_output(qt_app, tmp_path):
    from ui.views.results_view import ResultsView

    lines = [f"[ts] You have slain mob{i}!" for i in range(50)]
    kill_list, zone_list, summary = log_parser.parse_log_lines(lines)
    sections = summary_formatter.build_summary_sections(
        kill_list, zone_list, summary, "Gorrek"
    )

    offscreen = ResultsView()
    offscreen.setAttribute(Qt.WA_DontShowOnScreen, True)
    offscreen.setFixedSize(320, 240)
    offscreen.set_results(_SAMPLE_MAP, sections)
    offscreen.show()

    gen = video_generator.VideoGenerator(
        "Gorrek", zone_list, summary, target_seconds=2, fps=24
    )
    output = tmp_path / "out.mp4"
    worker = VideoWorker(gen, offscreen, output, fps=24)

    result = {}
    loop = QEventLoop()
    worker.finished.connect(lambda p: (result.__setitem__("ok", p), loop.quit()))
    worker.canceled.connect(lambda: (result.__setitem__("cancel", True), loop.quit()))
    # Cancel almost immediately, after the first frame is scheduled.
    worker.progress.connect(lambda *_: worker.cancel())
    worker.start()
    loop.exec()

    assert result.get("cancel") is True
    assert not output.exists()


def test_worker_finalize_failure_reports_error(qt_app, tmp_path, monkeypatch):
    import ui.video_worker as vw
    from ui.views.results_view import ResultsView

    lines = ["[ts] You have slain a mob!"]
    kill_list, zone_list, summary = log_parser.parse_log_lines(lines)
    sections = summary_formatter.build_summary_sections(
        kill_list, zone_list, summary, "Gorrek"
    )

    offscreen = ResultsView()
    offscreen.setAttribute(Qt.WA_DontShowOnScreen, True)
    offscreen.setFixedSize(320, 240)
    offscreen.set_results(_SAMPLE_MAP, sections)
    offscreen.show()

    gen = video_generator.VideoGenerator(
        "Gorrek", zone_list, summary, target_seconds=1, fps=2
    )
    output = tmp_path / "out.mp4"
    output.write_bytes(b"partial")  # pretend ffmpeg began writing the file

    class _FakeWriter:
        def append_data(self, frame):
            pass

        def close(self):
            raise RuntimeError("ffmpeg finalize failed")

    monkeypatch.setattr(vw.imageio, "get_writer", lambda *a, **k: _FakeWriter())

    worker = VideoWorker(gen, offscreen, output, fps=2)

    result = {}
    loop = QEventLoop()
    worker.finished.connect(lambda p: (result.__setitem__("ok", p), loop.quit()))
    worker.error.connect(lambda m: (result.__setitem__("err", m), loop.quit()))
    worker.start()
    loop.exec()

    # A close() failure means the file was never finalized: report error, not
    # a false success, and remove the partial output.
    assert "ok" not in result
    assert "ffmpeg finalize failed" in result.get("err", "")
    assert not output.exists()
