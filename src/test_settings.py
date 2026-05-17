from pathlib import Path

from PySide6.QtCore import QSettings

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
