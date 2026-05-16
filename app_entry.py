"""Frozen-app entry point for PyInstaller.

Exists at the repo root (next to ``EQTravelMap.spec``) so the bundled executable
has a single, predictable launch script. The real GUI lives in
``src/ui/app.py`` -- this file just makes the bare ``import ui.app`` style
imports the project uses today work in both source and frozen layouts.
"""

import sys
from pathlib import Path


def _src_dir():
    if hasattr(sys, "_MEIPASS"):
        # PyInstaller extracts source modules into _MEIPASS at runtime.
        return Path(sys._MEIPASS)
    return Path(__file__).resolve().parent / "src"


sys.path.insert(0, str(_src_dir()))

from ui.app import main  # noqa: E402

if __name__ == "__main__":
    main()
