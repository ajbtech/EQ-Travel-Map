from pathlib import Path

import resource_paths


def _project_root():
    return resource_paths.bundled_root() or Path(__file__).resolve().parents[2]


def project_asset(name):
    return _project_root() / "assets" / name


def theme_dir():
    bundle = resource_paths.bundled_root()
    if bundle is not None:
        return bundle / "ui" / "theme"
    return Path(__file__).resolve().parent / "theme"


def theme_asset(name):
    return theme_dir() / "assets" / name


def licenses_dir():
    return _project_root() / "LICENSES"


def to_qss_url(path):
    return str(Path(path)).replace("\\", "/")
