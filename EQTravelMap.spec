# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec for the EverQuest Travel Map desktop app.

Build with: ``pyinstaller EQTravelMap.spec`` from the repo root.

Mode: ``--onedir`` (required by Qt LGPL terms -- see ``LICENSES/README.md``).
The resulting ``dist/EQTravelMap/`` folder is what gets zipped and attached to
GitHub Releases for download by non-CLI users.
"""

from pathlib import Path


PROJECT_ROOT = Path(SPECPATH).resolve()
SRC_DIR = PROJECT_ROOT / "src"

# (source on disk, target directory inside the bundle)
DATAS = [
    (str(PROJECT_ROOT / "assets"), "assets"),
    (str(PROJECT_ROOT / "samples"), "samples"),
    (str(PROJECT_ROOT / "LICENSES"), "LICENSES"),
    (str(SRC_DIR / "ui" / "theme"), "ui/theme"),
    (str(PROJECT_ROOT / "zone_graph.json"), "."),
    (str(PROJECT_ROOT / "zone_map.png"), "."),
]

# Bare ``import eq_parser`` etc. only resolve once ``src/`` is on sys.path.
# The entry script handles that at runtime, but PyInstaller's static analysis
# also needs to know the modules exist.
HIDDEN_IMPORTS = [
    "eq_parser",
    "log_parser",
    "line_reader",
    "eq_display",
    "eq_list",
    "map_path",
    "money_sorter",
    "summary_formatter",
    "zone_graph",
    "ui.app",
    "ui.asset_paths",
    "ui.main_window",
    "ui.parse_worker",
    "ui.views.input_view",
    "ui.views.progress_view",
    "ui.views.results_view",
    "ui.widgets.engraved_heading",
    "ui.widgets.map_canvas",
    "ui.widgets.parchment_panel",
]


a = Analysis(
    ["app_entry.py"],
    pathex=[str(SRC_DIR)],
    binaries=[],
    datas=DATAS,
    hiddenimports=HIDDEN_IMPORTS,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=["tkinter"],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="EQTravelMap",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=str(PROJECT_ROOT / "assets" / "icon.ico"),
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name="EQTravelMap",
)
