from pathlib import Path

import summary_formatter
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
