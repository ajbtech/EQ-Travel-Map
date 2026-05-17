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
