import sys
from pathlib import Path


def _project_root():
    if hasattr(sys, "_MEIPASS"):
        return Path(sys._MEIPASS)
    return Path(__file__).resolve().parents[2]


def project_asset(name):
    return _project_root() / "assets" / name


def theme_dir():
    if hasattr(sys, "_MEIPASS"):
        return Path(sys._MEIPASS) / "ui" / "theme"
    return Path(__file__).resolve().parent / "theme"


def theme_asset(name):
    return theme_dir() / "assets" / name


def licenses_dir():
    return _project_root() / "LICENSES"


def to_qss_url(path):
    return str(Path(path)).replace("\\", "/")
