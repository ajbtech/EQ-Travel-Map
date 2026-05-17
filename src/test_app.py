"""Tests for the desktop app's bootstrap helpers.

`_load_stylesheet` `.format()`s the QSS template, so a placeholder drift
in `eq_theme.qss` would crash app startup with KeyError. The argparse
helper is similarly small but worth pinning so `--log-folder` and
`--output` defaults don't silently change.
"""

from pathlib import Path

import summary_formatter
from ui import app


def test_load_stylesheet_resolves_all_known_placeholders(qt_app):
    previous = qt_app.styleSheet()
    try:
        app._load_stylesheet(qt_app)
        assert qt_app.styleSheet() != ""
    finally:
        qt_app.setStyleSheet(previous)


def test_load_stylesheet_no_ops_when_theme_missing(qt_app, monkeypatch, tmp_path):
    monkeypatch.setattr(app.asset_paths, "theme_dir", lambda: tmp_path)
    previous = qt_app.styleSheet()
    try:
        qt_app.setStyleSheet("/* sentinel */")
        app._load_stylesheet(qt_app)
        assert qt_app.styleSheet() == "/* sentinel */"
    finally:
        qt_app.setStyleSheet(previous)


def test_build_arg_parser_accepts_character_and_paths():
    parser = app.build_arg_parser()

    args = parser.parse_args(
        ["Gorrek", "--log-folder", "/tmp/logs", "--output", "/tmp/out.png"]
    )

    assert args.character_name == "Gorrek"
    assert args.log_folder == Path("/tmp/logs")
    assert args.output == Path("/tmp/out.png")


def test_build_arg_parser_character_is_optional():
    parser = app.build_arg_parser()

    args = parser.parse_args([])

    assert args.character_name is None


def test_build_arg_parser_log_folder_defaults_to_none():
    # None signals "no explicit override" so run() can fall through to a
    # persisted value before the built-in default.
    parser = app.build_arg_parser()

    args = parser.parse_args([])

    assert args.log_folder is None


def test_resolve_log_folder_prefers_cli_override(monkeypatch):
    monkeypatch.setattr(app.settings, "load_log_folder", lambda: Path("/persisted"))

    resolved = app._resolve_log_folder(Path("/explicit"))

    assert resolved == Path("/explicit")


def test_resolve_log_folder_uses_persisted_when_no_cli_override(monkeypatch):
    monkeypatch.setattr(app.settings, "load_log_folder", lambda: Path("/persisted"))

    resolved = app._resolve_log_folder(None)

    assert resolved == Path("/persisted")


def test_resolve_log_folder_falls_back_to_built_in_default(monkeypatch):
    monkeypatch.setattr(app.settings, "load_log_folder", lambda: None)

    resolved = app._resolve_log_folder(None)

    assert resolved == Path(app.eq_parser.DEFAULT_LOG_FOLDER_PATH)


def test_infer_character_names_returns_sorted_unique_names(tmp_path):
    (tmp_path / "eqlog_Gorrek_P1999Green.txt").write_text("")
    (tmp_path / "ARCHIVEeqlog_Gorrek_P1999Green.txt").write_text("")
    (tmp_path / "eqlog_Aelinor_P1999Green.txt").write_text("")
    (tmp_path / "not_an_eq_log.txt").write_text("")

    names = app._infer_character_names(tmp_path)

    assert names == ["Aelinor", "Gorrek"]


def test_default_character_name_returns_sole_name_else_empty(tmp_path):
    (tmp_path / "eqlog_Gorrek_P1999Green.txt").write_text("")
    assert app._default_character_name(tmp_path) == "Gorrek"

    (tmp_path / "eqlog_Aelinor_P1999Green.txt").write_text("")
    assert app._default_character_name(tmp_path) == ""


def _sample_sections():
    return summary_formatter.SummarySections(
        character_line="Character: Gorrek",
        top_kills_lines=["Top 5 killed creatures:"],
        top_zones_lines=["Top 5 visited zones:"],
        stats_lines=["Total logs: 99"],
    )


def test_restore_last_results_shows_results_view_when_state_valid(qt_app, tmp_path):
    image_path = tmp_path / "map.png"
    image_path.write_bytes(b"PNG")
    sections = _sample_sections()

    window = _StubWindow()
    cleared = []

    app._restore_last_results(
        window,
        cli_character=None,
        load_last_results=lambda: ("Gorrek", image_path, sections),
        clear_last_results=lambda: cleared.append(True),
    )

    assert window.shown == [("results", image_path, sections)]
    assert cleared == []


def test_restore_last_results_skips_when_no_persisted_state(qt_app, tmp_path):
    window = _StubWindow()
    cleared = []

    app._restore_last_results(
        window,
        cli_character=None,
        load_last_results=lambda: None,
        clear_last_results=lambda: cleared.append(True),
    )

    assert window.shown == []
    assert cleared == []


def test_restore_last_results_skips_when_cli_character_provided(qt_app, tmp_path):
    image_path = tmp_path / "map.png"
    image_path.write_bytes(b"PNG")
    sections = _sample_sections()

    window = _StubWindow()
    cleared = []

    app._restore_last_results(
        window,
        cli_character="Mortimer",
        load_last_results=lambda: ("Gorrek", image_path, sections),
        clear_last_results=lambda: cleared.append(True),
    )

    assert window.shown == []
    assert cleared == []


def test_restore_last_results_clears_when_image_missing(qt_app, tmp_path):
    image_path = tmp_path / "gone.png"  # never created
    sections = _sample_sections()

    window = _StubWindow()
    cleared = []

    app._restore_last_results(
        window,
        cli_character=None,
        load_last_results=lambda: ("Gorrek", image_path, sections),
        clear_last_results=lambda: cleared.append(True),
    )

    assert window.shown == []
    assert cleared == [True]


class _StubWindow:
    def __init__(self):
        self.shown = []

    def show_results(self, image_path, sections):
        self.shown.append(("results", image_path, sections))
