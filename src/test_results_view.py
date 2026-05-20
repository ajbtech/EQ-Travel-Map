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


def test_character_heading_shows_name(qt_app):
    view = ResultsView()
    view.set_results(Path("/tmp/map.png"), _sections("Gorrek"))
    assert view.character_heading.text() == "Gorrek"


def test_character_heading_blank_without_character(qt_app):
    view = ResultsView()
    view.set_results(Path("/tmp/map.png"), _sections(""))
    assert view.character_heading.text() == ""


def test_character_heading_matches_input_title_style(qt_app):
    from PySide6.QtGui import QColor

    view = ResultsView()
    assert view.character_heading._fill == QColor("#2a1c0e")
    assert view.character_heading._engraved is False
    assert view.character_heading.font().family() == "Georgia"
    assert view.character_heading.font().bold()


def test_character_heading_is_centered(qt_app):
    from PySide6.QtCore import Qt

    view = ResultsView()
    assert view.character_heading._alignment & Qt.AlignHCenter


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
