import sys
from pathlib import Path

from ui import asset_paths


def test_project_asset_returns_path_ending_in_assets_and_name():
    result = asset_paths.project_asset("zone_map.png")
    assert result.name == "zone_map.png"
    assert result.parent.name == "assets"


def test_theme_asset_returns_path_under_theme():
    result = asset_paths.theme_asset("stone.png")
    assert result.name == "stone.png"
    assert "theme" in str(result)


def test_to_qss_url_uses_forward_slashes():
    path = Path("/some/path/to/file.png")
    result = asset_paths.to_qss_url(path)
    assert "\\" not in result
    assert "/" in result


def test_project_asset_resolves_correctly_in_dev_mode(monkeypatch):
    monkeypatch.delattr(sys, "_MEIPASS", raising=False)
    result = asset_paths.project_asset("zone_map.png")
    # asset_paths.py is in src/ui/; parents[2] is the project root
    expected = Path(__file__).resolve().parents[1] / "assets" / "zone_map.png"
    assert result == expected


def test_project_asset_uses_meipass_in_bundle(monkeypatch, tmp_path):
    monkeypatch.setattr(sys, "_MEIPASS", str(tmp_path), raising=False)
    result = asset_paths.project_asset("icon.ico")
    assert result == tmp_path / "assets" / "icon.ico"


def test_theme_dir_uses_meipass_in_bundle(monkeypatch, tmp_path):
    monkeypatch.setattr(sys, "_MEIPASS", str(tmp_path), raising=False)
    assert asset_paths.theme_dir() == tmp_path / "ui" / "theme"


def test_licenses_dir_is_under_project_root(monkeypatch):
    monkeypatch.delattr(sys, "_MEIPASS", raising=False)
    result = asset_paths.licenses_dir()
    assert result.name == "LICENSES"
