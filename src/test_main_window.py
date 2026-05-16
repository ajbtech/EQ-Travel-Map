from pathlib import Path

from PySide6.QtCore import QSize
from PySide6.QtGui import QCloseEvent

import summary_formatter
from ui.main_window import MainWindow, _split_error_message
from ui.parse_worker import ParseWorker


class _FakeSettings:
    def __init__(self, initial=None):
        self._values = dict(initial or {})

    def value(self, key, default=None):
        return self._values.get(key, default)

    def setValue(self, key, value):
        self._values[key] = value


def _sections(character="Gorrek", stats_lines=None):
    return summary_formatter.SummarySections(
        character_line=f"Character: {character}",
        top_kills_lines=["Top 5 killed creatures:"],
        top_zones_lines=["Top 5 visited zones:"],
        stats_lines=stats_lines or ["Total logs: 0"],
    )


def _make_window(qt_app, **overrides):
    errors_shown = []

    def fake_error_dialog(title, message):
        errors_shown.append((title, message))

    workers_built = []

    def default_worker_factory(character, folder, output):
        worker = ParseWorker(
            character,
            folder,
            output,
            parse_fn=lambda *_args, **_kwargs: (None, None, None),
            draw_fn=lambda *_args, **_kwargs: None,
            summary_fn=lambda *_args, **_kwargs: [],
        )
        workers_built.append(worker)
        return worker

    window = MainWindow(
        default_log_folder=Path("/logs"),
        default_output_path=Path("/tmp/out.png"),
        default_character_name="Gorrek",
        worker_factory=overrides.get("worker_factory", default_worker_factory),
        run_worker=overrides.get("run_worker", lambda worker: worker.run()),
        error_dialog=overrides.get("error_dialog", fake_error_dialog),
        settings=overrides.get("settings", _FakeSettings()),
    )
    window._test_workers = workers_built
    window._test_errors = errors_shown
    return window


def test_initial_view_is_input(qt_app):
    window = _make_window(qt_app)

    assert window.current_view_name == "input"


def test_split_error_message_classifies_missing_log_files():
    summary, detail = _split_error_message(
        "FileNotFoundError: no log files matching eqlog_Gorrek_*.txt"
    )

    assert "No log files were found" in summary
    assert "eqlog_Gorrek" in detail


def test_split_error_message_classifies_permission_denied():
    summary, detail = _split_error_message(
        "PermissionError: [Errno 13] Permission denied: 'eqlog.txt'"
    )

    assert "couldn't read" in summary
    assert "Permission denied" in detail


def test_split_error_message_falls_back_to_generic_for_unknown_error():
    summary, detail = _split_error_message("KaboomError: something weird")

    assert "Something went wrong" in summary
    assert detail == "KaboomError: something weird"


def test_split_error_message_handles_empty_input():
    summary, detail = _split_error_message("")

    assert "Something went wrong" in summary
    assert detail == ""


def test_show_progress_switches_to_progress_view(qt_app):
    window = _make_window(qt_app)

    window.show_progress("Mortimer")

    assert window.current_view_name == "progress"
    assert "Mortimer" in window.progress_view.character_label.text()


def test_show_results_switches_to_results_view(qt_app):
    window = _make_window(qt_app)

    sections = _sections(stats_lines=["Total logs: 99", "Kill Count: 17"])
    window.show_results(Path("/tmp/out.png"), sections)

    assert window.current_view_name == "results"
    assert "Kill Count: 17" in window.results_view.summary_text()


def test_progress_signal_updates_progress_view(qt_app):
    window = _make_window(qt_app)
    window.show_progress("Gorrek")

    window._on_worker_progress("eqlog_Gorrek_P1999Green.txt", 12345)

    assert "eqlog_Gorrek_P1999Green.txt" in window.progress_view.file_label.text()
    assert "12,345" in window.progress_view.lines_label.text()


def test_parse_requested_runs_worker_and_routes_finished_to_results(qt_app):
    sections = _sections(stats_lines=["Kill Count: 9001"])

    def parse_fn(folder, name, progress_cb):
        return None, None, None

    def draw_fn(zones, output_path):
        return None

    def summary_fn(*_args, **_kwargs):
        return sections

    def factory(character, folder, output):
        return ParseWorker(
            character,
            folder,
            output,
            parse_fn=parse_fn,
            draw_fn=draw_fn,
            summary_fn=summary_fn,
        )

    window = _make_window(qt_app, worker_factory=factory)

    window.input_view.parse_requested.emit("Gorrek", "/logs", "/tmp/out.png")

    assert window.current_view_name == "results"
    assert "Kill Count: 9001" in window.results_view.summary_text()


def test_parse_requested_routes_error_to_input_view_with_dialog(qt_app):
    def parse_fn(folder, name, progress_cb):
        raise RuntimeError("disk on fire")

    def factory(character, folder, output):
        return ParseWorker(character, folder, output, parse_fn=parse_fn)

    window = _make_window(qt_app, worker_factory=factory)

    window.input_view.parse_requested.emit("Gorrek", "/logs", "/tmp/out.png")

    assert window.current_view_name == "input"
    assert window._test_errors == [("Parse failed", "disk on fire")]


def test_parse_requested_routes_canceled_back_to_input(qt_app):
    def parse_fn(folder, name, progress_cb):
        progress_cb(_ProgressStub("file.txt", 100))
        return None, None, None

    def factory(character, folder, output):
        worker = ParseWorker(character, folder, output, parse_fn=parse_fn)
        worker.cancel()
        return worker

    window = _make_window(qt_app, worker_factory=factory)

    window.input_view.parse_requested.emit("Gorrek", "/logs", "/tmp/out.png")

    assert window.current_view_name == "input"


def test_progress_view_cancel_button_invokes_worker_cancel(qt_app):
    cancel_calls = []

    def parse_fn(folder, name, progress_cb):
        return None, None, None

    def factory(character, folder, output):
        worker = ParseWorker(character, folder, output, parse_fn=parse_fn)
        original_cancel = worker.cancel

        def tracked_cancel():
            cancel_calls.append(True)
            original_cancel()

        worker.cancel = tracked_cancel
        return worker

    captured = {}

    def deferred_run(worker):
        captured["worker"] = worker

    window = _make_window(qt_app, worker_factory=factory, run_worker=deferred_run)

    window.input_view.parse_requested.emit("Gorrek", "/logs", "/tmp/out.png")

    window.progress_view.cancel_requested.emit()

    assert cancel_calls == [True]


def test_results_view_back_button_returns_to_input(qt_app):
    window = _make_window(qt_app)
    window.show_results(Path("/tmp/out.png"), _sections())

    window.results_view.back_requested.emit()

    assert window.current_view_name == "input"


def test_window_resizes_to_each_view_preferred_size(qt_app):
    window = _make_window(qt_app)
    window.show()

    assert window.size().toTuple() == window.input_view.preferred_window_size

    window.show_progress("Gorrek")
    assert window.size().toTuple() == window.progress_view.preferred_window_size

    window.show_results(Path("/tmp/out.png"), _sections())
    assert window.size().toTuple() == window.results_view.preferred_window_size

    window.show_input()
    assert window.size().toTuple() == window.input_view.preferred_window_size


def test_results_view_is_freely_resizable(qt_app):
    window = _make_window(qt_app)
    window.show()
    window.show_results(Path("/tmp/out.png"), _sections())

    min_w, min_h = window.results_view.minimum_window_size
    assert window.minimumSize().toTuple() == (min_w, min_h)
    # Maximum size should be unconstrained (Qt's QWIDGETSIZE_MAX sentinel).
    assert window.maximumSize().width() >= (1 << 24) - 1
    assert window.maximumSize().height() >= (1 << 24) - 1


def test_input_and_progress_views_remain_fixed_size(qt_app):
    window = _make_window(qt_app)
    window.show()

    in_w, in_h = window.input_view.preferred_window_size
    assert window.minimumSize().toTuple() == (in_w, in_h)
    assert window.maximumSize().toTuple() == (in_w, in_h)

    window.show_progress("Gorrek")
    pg_w, pg_h = window.progress_view.preferred_window_size
    assert window.minimumSize().toTuple() == (pg_w, pg_h)
    assert window.maximumSize().toTuple() == (pg_w, pg_h)


def test_results_view_restores_saved_size_from_settings(qt_app):
    saved = QSize(1500, 900)
    settings = _FakeSettings({"results/size": saved})
    window = _make_window(qt_app, settings=settings)
    window.show()

    window.show_results(Path("/tmp/out.png"), _sections())

    assert window.size().toTuple() == (1500, 900)


def test_results_view_uses_preferred_size_when_no_saved_size(qt_app):
    window = _make_window(qt_app, settings=_FakeSettings())
    window.show()

    window.show_results(Path("/tmp/out.png"), _sections())

    assert window.size().toTuple() == window.results_view.preferred_window_size


def test_saved_size_below_minimum_is_clamped_up(qt_app):
    settings = _FakeSettings({"results/size": QSize(100, 100)})
    window = _make_window(qt_app, settings=settings)
    window.show()

    window.show_results(Path("/tmp/out.png"), _sections())

    min_w, min_h = window.results_view.minimum_window_size
    assert window.size().width() >= min_w
    assert window.size().height() >= min_h


def test_close_persists_last_results_size(qt_app):
    settings = _FakeSettings()
    window = _make_window(qt_app, settings=settings)
    window.show()
    window.show_results(Path("/tmp/out.png"), _sections())

    window.resize(1400, 850)
    # Forced resize fires resizeEvent synchronously in Qt; the new size is
    # captured by MainWindow.resizeEvent for persistence on close.
    window.closeEvent(QCloseEvent())

    saved = settings.value("results/size")
    assert isinstance(saved, QSize)
    assert saved.toTuple() == (1400, 850)


def test_close_does_not_persist_when_results_never_shown(qt_app):
    settings = _FakeSettings()
    window = _make_window(qt_app)
    window.show()

    window.closeEvent(QCloseEvent())

    assert settings.value("results/size") is None


class _ProgressStub:
    def __init__(self, name, count):
        from pathlib import Path as _Path

        self.file_path = _Path(name)
        self.line_count = count
