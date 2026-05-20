from pathlib import Path

import log_parser
import summary_formatter
from eq_list import EQList
from ui.views.results_view import ResultsView


def _sections(character="Gorrek"):
    return summary_formatter.SummarySections(
        character_line=f"Character: {character}" if character else "",
        top_kills_lines=["Top 5 killed creatures:"],
        top_zones_lines=["Top 5 visited zones:"],
        stats_lines=["Total logs: 0"],
    )


def test_suggested_save_filename_prefixes_character_name(qt_app):
    view = ResultsView()
    view.set_results(Path("/tmp/everquest_travel_map.png"), _sections("Gorrek"))
    assert view._suggested_save_filename() == "Gorrek_everquest_travel_map.png"


def test_suggested_save_filename_without_character_returns_original(qt_app):
    view = ResultsView()
    view.set_results(Path("/tmp/everquest_travel_map.png"), _sections(""))
    assert view._suggested_save_filename() == "everquest_travel_map.png"


def test_map_frame_width_matches_image_aspect_ratio(qt_app):
    sample_image = Path(__file__).resolve().parents[1] / "docs" / "sample_map.png"
    view = ResultsView()
    view.resize(1200, 700)
    view.set_results(sample_image, _sections())
    qt_app.processEvents()

    border = ResultsView._MAP_FRAME_BORDER
    aspect = view.map_canvas.source_aspect_ratio()
    assert aspect is not None
    inner_h = view.map_frame.height() - 2 * border
    expected_width = int(round(inner_h * aspect)) + 2 * border
    assert view.map_frame.width() == expected_width


def test_summary_frame_spans_map_and_buttons(qt_app):
    sample_image = Path(__file__).resolve().parents[1] / "docs" / "sample_map.png"
    view = ResultsView()
    view.resize(1200, 700)
    view.set_results(sample_image, _sections())
    qt_app.processEvents()

    expected = view.map_frame.width() + view.button_frame.sizeHint().width()
    assert view.summary_stone_frame.width() == expected


def test_make_video_button_disabled_without_timeline(qt_app):
    view = ResultsView()
    view.set_results(Path("/tmp/map.png"), _sections())
    assert not view.make_video_button.isEnabled()


def test_make_video_button_enabled_with_zone_list_and_summary(qt_app):
    zone_list = EQList()
    zone_list.add("Grobb")
    summary = log_parser.build_empty_summary()
    view = ResultsView()
    view.set_results(Path("/tmp/map.png"), _sections(), zone_list, summary)
    assert view.make_video_button.isEnabled()


def test_suggested_video_filename_uses_character(qt_app):
    view = ResultsView()
    view.set_results(Path("/tmp/map.png"), _sections("Gorrek"))
    assert view._suggested_video_filename() == "Gorrek_travel.mp4"


def test_make_video_setup_failure_surfaces_error_dialog(qt_app, monkeypatch):
    from ui.views import results_view as rv

    sample_image = Path(__file__).resolve().parents[1] / "docs" / "sample_map.png"
    zone_list = EQList()
    zone_list.add("Grobb")
    summary = log_parser.build_empty_summary()
    view = ResultsView()
    view.set_results(sample_image, _sections("Gorrek"), zone_list, summary)

    # Skip the two interactive dialogs.
    monkeypatch.setattr(rv._DurationDialog, "exec", lambda self: rv.QDialog.Accepted)
    monkeypatch.setattr(rv._DurationDialog, "target_seconds", lambda self: 30)
    monkeypatch.setattr(
        rv.QFileDialog,
        "getSaveFileName",
        staticmethod(lambda *a, **k: ("/tmp/o.mp4", "")),
    )

    # Force the export setup to blow up the way a missing dependency would.
    def _boom(self, *_a, **_k):
        raise RuntimeError("ffmpeg unavailable")

    monkeypatch.setattr(rv.ResultsView, "_start_video_export", _boom)

    captured = {}
    monkeypatch.setattr(
        rv.QMessageBox,
        "warning",
        staticmethod(lambda *a, **k: captured.setdefault("args", a)),
    )

    view._on_make_video()

    # The failure must reach the user instead of vanishing silently.
    assert "args" in captured
    assert "ffmpeg unavailable" in captured["args"][-1]
