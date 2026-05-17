import summary_formatter
from ui.views.more_stats_view import MoreStatsDialog


def _sections():
    return summary_formatter.SummarySections(
        character_line="Character: Gorrek",
        top_kills_lines=["Top 5 killed creatures:", "1. ghoul: 3"],
        top_zones_lines=["Top 5 visited zones:", "1. Grobb: 5"],
        stats_lines=["Total logs: 0"],
        extended_kills_lines=["Top 25 killed creatures:", "1. ghoul: 30"],
        extended_zones_lines=["Top 25 visited zones:", "1. Grobb: 10"],
        extended_spells_lines=["Top 25 cast spells:", "1. Spirit of Wolf: 10"],
        max_damage_lines=["Max hit by damage type:", "slash: 25"],
    )


def test_more_stats_dialog_opens_without_error(qt_app):
    dlg = MoreStatsDialog(_sections())
    assert dlg is not None


def test_more_stats_dialog_is_not_modal(qt_app):
    dlg = MoreStatsDialog(_sections())
    assert not dlg.isModal()


def test_more_stats_dialog_has_expected_title(qt_app):
    dlg = MoreStatsDialog(_sections())
    assert dlg.windowTitle() == "More Statistics"


def test_more_stats_dialog_renders_all_four_sections(qt_app):
    from PySide6.QtWidgets import QLabel

    dlg = MoreStatsDialog(_sections())
    labels = dlg.findChildren(QLabel)
    all_text = " ".join(lbl.text() for lbl in labels)
    assert "Top 25 visited zones" in all_text
    assert "Top 25 killed creatures" in all_text
    assert "Top 25 cast spells" in all_text
    assert "Max hit by damage type" in all_text


def test_more_stats_dialog_on_more_stats_noop_without_sections(qt_app):
    from ui.views.results_view import ResultsView

    view = ResultsView()
    view._on_more_stats()  # Should not raise when _current_sections is None


def test_more_stats_button_exists_in_results_view(qt_app):
    from ui.views.results_view import ResultsView

    view = ResultsView()
    assert hasattr(view, "more_stats_button")


def test_more_stats_button_label(qt_app):
    from ui.views.results_view import ResultsView

    view = ResultsView()
    assert view.more_stats_button.text() == "MORE STATS"
