"""Single source of truth for the PyInstaller bundle convention.

When frozen by PyInstaller, bundled data lives under ``sys._MEIPASS``; in a
normal source checkout it lives relative to the package. Modules that need to
locate data/asset files (``eq_display``, ``zone_graph``, ``ui.asset_paths``)
share ``bundled_root`` so the ``sys._MEIPASS`` check lives in exactly one place.
"""

import sys
from pathlib import Path


def bundled_root():
    """Return the PyInstaller bundle root when frozen, else ``None``.

    Callers fall back to their own source-relative path when this is ``None``,
    so each module keeps ownership of its dev-mode layout while the frozen
    convention stays centralized here.
    """
    meipass = getattr(sys, "_MEIPASS", None)
    return Path(meipass) if meipass else None
