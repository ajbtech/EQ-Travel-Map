from pathlib import Path

import log_parser
import summary_formatter
from ui.parse_worker import ParseWorker


class _FakeList:
    """Stand-in for EQList; only `get_raw_eq_list` is used by the draw stub."""

    def __init__(self, items=None):
        self._items = list(items or [])

    def get_raw_eq_list(self):
        return list(self._items)


def _make_worker(qt_app, **overrides):
    parse_calls = []
    draw_calls = []
    summary_calls = []

    kill_list = _FakeList()
    zone_list = _FakeList(["Grobb"])
    summary = log_parser.build_empty_summary()
    summary_sections = summary_formatter.SummarySections(
        character_line="Character: Gorrek",
        top_kills_lines=["Top 5 killed creatures:"],
        top_zones_lines=["Top 5 visited zones:", "1. Grobb: 1"],
        stats_lines=["Total logs: 0"],
    )

    def default_parse(folder, name, progress_cb):
        parse_calls.append((folder, name))
        return kill_list, zone_list, summary

    def default_draw(zones, output_path):
        draw_calls.append((zones, output_path))

    def default_summary(kills, zones, summ, name):
        summary_calls.append((kills, zones, summ, name))
        return summary_sections

    worker = ParseWorker(
        character_name="Gorrek",
        log_folder_path="/logs",
        output_path="/tmp/out.png",
        parse_fn=overrides.get("parse_fn", default_parse),
        draw_fn=overrides.get("draw_fn", default_draw),
        summary_fn=overrides.get("summary_fn", default_summary),
    )
    worker._test_calls = {
        "parse": parse_calls,
        "draw": draw_calls,
        "summary": summary_calls,
    }
    worker._test_summary_sections = summary_sections
    return worker


def _spy(signal):
    received = []
    signal.connect(lambda *args: received.append(args))
    return received


def test_run_emits_finished_with_output_path_and_summary_sections(qt_app):
    worker = _make_worker(qt_app)
    finished = _spy(worker.finished)

    worker.run()

    assert len(finished) == 1
    output_path, summary_sections = finished[0]
    assert output_path == Path("/tmp/out.png")
    assert summary_sections == worker._test_summary_sections


def test_run_calls_parse_then_summary_then_draw_in_order(qt_app):
    order = []

    def parse(folder, name, progress_cb):
        order.append("parse")
        return _FakeList(), _FakeList(), log_parser.build_empty_summary()

    def summary(kills, zones, summ, name):
        order.append("summary")
        return summary_formatter.SummarySections()

    def draw(zones, output_path):
        order.append("draw")

    worker = _make_worker(qt_app, parse_fn=parse, summary_fn=summary, draw_fn=draw)

    worker.run()

    assert order == ["parse", "summary", "draw"]


def test_progress_callback_emits_progress_signal(qt_app):
    def parse(folder, name, progress_cb):
        progress_cb(log_parser.ParseProgress(Path("ARCHIVEeqlog_Gorrek.txt"), 5000))
        progress_cb(log_parser.ParseProgress(Path("ARCHIVE2eqlog_Gorrek.txt"), 12000))
        return _FakeList(), _FakeList(), log_parser.build_empty_summary()

    worker = _make_worker(qt_app, parse_fn=parse)
    progress = _spy(worker.progress)

    worker.run()

    assert progress == [
        ("ARCHIVEeqlog_Gorrek.txt", 5000),
        ("ARCHIVE2eqlog_Gorrek.txt", 12000),
    ]


def test_run_emits_error_when_parse_raises(qt_app):
    def parse(folder, name, progress_cb):
        raise RuntimeError("disk on fire")

    worker = _make_worker(qt_app, parse_fn=parse)
    error = _spy(worker.error)
    finished = _spy(worker.finished)

    worker.run()

    assert error == [("disk on fire",)]
    assert finished == []


def test_run_emits_error_when_draw_raises(qt_app):
    def draw(zones, output_path):
        raise RuntimeError("PIL exploded")

    worker = _make_worker(qt_app, draw_fn=draw)
    error = _spy(worker.error)
    finished = _spy(worker.finished)

    worker.run()

    assert error == [("PIL exploded",)]
    assert finished == []


def test_cancel_during_parse_emits_canceled_and_skips_finished(qt_app):
    progress_calls = []

    def parse(folder, name, progress_cb):
        progress_calls.append(1)
        progress_cb(log_parser.ParseProgress(Path("file.txt"), 100))
        progress_calls.append(2)  # should not get here if cancellation worked
        return _FakeList(), _FakeList(), log_parser.build_empty_summary()

    worker = _make_worker(qt_app, parse_fn=parse)
    canceled = _spy(worker.canceled)
    finished = _spy(worker.finished)

    worker.cancel()
    worker.run()

    assert canceled == [()]
    assert finished == []
    assert progress_calls == [1]


def test_cancel_after_run_completes_does_not_emit_canceled(qt_app):
    worker = _make_worker(qt_app)
    canceled = _spy(worker.canceled)

    worker.run()
    worker.cancel()

    assert canceled == []
