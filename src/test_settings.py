from pathlib import Path

from PySide6.QtCore import QSettings

import summary_formatter
from ui import settings


def _redirect_to_ini(monkeypatch, tmp_path):
    ini_path = tmp_path / "settings.ini"
    monkeypatch.setattr(
        settings,
        "_make_settings",
        lambda: QSettings(str(ini_path), QSettings.IniFormat),
    )


def test_load_log_folder_returns_none_when_unset(qt_app, tmp_path, monkeypatch):
    _redirect_to_ini(monkeypatch, tmp_path)

    assert settings.load_log_folder() is None


def test_save_then_load_returns_saved_folder(qt_app, tmp_path, monkeypatch):
    _redirect_to_ini(monkeypatch, tmp_path)

    settings.save_log_folder(Path("/some/eq/logs"))

    assert settings.load_log_folder() == Path("/some/eq/logs")


def test_save_accepts_string_path(qt_app, tmp_path, monkeypatch):
    _redirect_to_ini(monkeypatch, tmp_path)

    settings.save_log_folder("/another/folder")

    assert settings.load_log_folder() == Path("/another/folder")


def test_save_overwrites_previous_value(qt_app, tmp_path, monkeypatch):
    _redirect_to_ini(monkeypatch, tmp_path)

    settings.save_log_folder(Path("/first"))
    settings.save_log_folder(Path("/second"))

    assert settings.load_log_folder() == Path("/second")


def _sample_sections():
    return summary_formatter.SummarySections(
        character_line="Character: Gorrek",
        top_kills_lines=["Top 5 killed creatures:", "1. a rat: 12"],
        top_zones_lines=["Top 5 visited zones:", "1. North Qeynos: 5"],
        stats_lines=["Total logs: 99", "Kill Count: 17"],
    )


def test_load_last_results_returns_none_when_unset(qt_app, tmp_path, monkeypatch):
    _redirect_to_ini(monkeypatch, tmp_path)

    assert settings.load_last_results() is None


def test_save_then_load_last_results_round_trip(qt_app, tmp_path, monkeypatch):
    _redirect_to_ini(monkeypatch, tmp_path)
    image_path = tmp_path / "map.png"
    image_path.write_bytes(b"PNG")
    sections = _sample_sections()

    settings.save_last_results("Gorrek", image_path, sections)
    loaded = settings.load_last_results()

    assert loaded is not None
    character, loaded_image, loaded_sections = loaded
    assert character == "Gorrek"
    assert loaded_image == image_path
    assert loaded_sections == sections


def test_load_last_results_returns_none_when_image_missing(
    qt_app, tmp_path, monkeypatch
):
    _redirect_to_ini(monkeypatch, tmp_path)
    image_path = tmp_path / "vanished.png"
    image_path.write_bytes(b"PNG")
    settings.save_last_results("Gorrek", image_path, _sample_sections())
    image_path.unlink()

    assert settings.load_last_results() is None


def test_load_last_results_clears_state_when_image_missing(
    qt_app, tmp_path, monkeypatch
):
    _redirect_to_ini(monkeypatch, tmp_path)
    image_path = tmp_path / "vanished.png"
    image_path.write_bytes(b"PNG")
    settings.save_last_results("Gorrek", image_path, _sample_sections())
    image_path.unlink()

    settings.load_last_results()

    # Re-create the image but the cleared state should still be gone.
    image_path.write_bytes(b"PNG")
    assert settings.load_last_results() is None


def test_clear_last_results_removes_persisted_state(qt_app, tmp_path, monkeypatch):
    _redirect_to_ini(monkeypatch, tmp_path)
    image_path = tmp_path / "map.png"
    image_path.write_bytes(b"PNG")
    settings.save_last_results("Gorrek", image_path, _sample_sections())

    settings.clear_last_results()

    assert settings.load_last_results() is None


def test_load_last_results_returns_none_on_corrupt_json(
    qt_app, tmp_path, monkeypatch
):
    _redirect_to_ini(monkeypatch, tmp_path)
    image_path = tmp_path / "map.png"
    image_path.write_bytes(b"PNG")
    settings.save_last_results("Gorrek", image_path, _sample_sections())
    # Corrupt the persisted sections JSON.
    settings._make_settings().setValue(
        settings._LAST_SUMMARY_SECTIONS_KEY, "{not valid json"
    )

    assert settings.load_last_results() is None
