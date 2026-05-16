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

# Qt modules the app does not use. The app only imports QtCore, QtGui, and
# QtWidgets, so every other Qt submodule -- and its accompanying native
# library, plugin folder, and QML resources -- can be stripped from the
# bundle. PyInstaller's PySide6 hook is permissive and pulls most of these
# in by default, so the resulting savings are significant (tens of MB).
UNUSED_QT_MODULES = [
    "Qt3DAnimation", "Qt3DCore", "Qt3DExtras", "Qt3DInput", "Qt3DLogic",
    "Qt3DQuick", "Qt3DQuickAnimation", "Qt3DQuickExtras", "Qt3DQuickInput",
    "Qt3DQuickRender", "Qt3DQuickScene2D", "Qt3DRender",
    "QtBluetooth", "QtCharts", "QtChartsQml",
    "QtConcurrent", "QtDBus",
    "QtDataVisualization", "QtDataVisualizationQml",
    "QtDesigner", "QtDesignerComponents",
    "QtHelp", "QtHttpServer",
    "QtMultimedia", "QtMultimediaQuick", "QtMultimediaWidgets",
    "QtNetwork", "QtNetworkAuth", "QtNfc",
    "QtOpenGL", "QtOpenGLWidgets",
    "QtPdf", "QtPdfQuick", "QtPdfWidgets",
    "QtPositioning", "QtPositioningQuick",
    "QtPrintSupport",
    "QtQml", "QtQmlCore", "QtQmlMeta", "QtQmlModels",
    "QtQmlWorkerScript", "QtQmlXmlListModel",
    "QtQuick", "QtQuick3D", "QtQuick3DAssetImport", "QtQuick3DAssetUtils",
    "QtQuick3DEffects", "QtQuick3DGlslParser", "QtQuick3DHelpers",
    "QtQuick3DHelpersImpl", "QtQuick3DIblBaker",
    "QtQuick3DParticleEffects", "QtQuick3DParticles",
    "QtQuick3DRuntimeRender", "QtQuick3DUtils",
    "QtQuick3DXr", "QtQuick3DXrHelpers", "QtQuick3DXrHelpersImpl",
    "QtQuickControls2", "QtQuickControls2Impl",
    "QtQuickDialogs2", "QtQuickDialogs2QuickImpl", "QtQuickDialogs2Utils",
    "QtQuickEffects", "QtQuickLayouts", "QtQuickParticles",
    "QtQuickShapes", "QtQuickTemplates2", "QtQuickTest",
    "QtQuickTimeline", "QtQuickWidgets",
    "QtRemoteObjects", "QtScxml", "QtScxmlQml",
    "QtSensors", "QtSensorsQuick",
    "QtSerialBus", "QtSerialPort",
    "QtSpatialAudio", "QtSql",
    "QtStateMachine", "QtStateMachineQml",
    "QtSvg", "QtSvgWidgets",
    "QtTest", "QtTextToSpeech",
    "QtUiTools", "QtVirtualKeyboard",
    "QtWebChannel", "QtWebChannelQuick",
    "QtWebEngineCore", "QtWebEngineQuick", "QtWebEngineWidgets",
    "QtWebSockets", "QtWebView", "QtWebViewQuick",
    "QtXml", "QtXmlPatterns",
]

# Qt plugin subfolders tied to the modules above. The platforms, styles,
# imageformats, iconengines, generic, and platformthemes folders are kept
# because QtWidgets needs them at runtime.
UNUSED_QT_PLUGIN_DIRS = [
    "3dinputdevices", "3drenderers", "assetimporters",
    "canbus", "designer", "geometryloaders",
    "multimedia", "networkinformation",
    "playlistformats", "position", "printsupport",
    "qmltooling", "renderers", "renderplugins",
    "sceneparsers", "scxmldatamodel",
    "sensorgestures", "sensors",
    "sqldrivers", "texttospeech", "tls",
    "virtualkeyboard", "webview",
]


def _is_excluded_qt(dest: str) -> bool:
    """Return True if a bundled entry belongs to an unused Qt module."""
    norm = dest.replace("\\", "/").lower()

    # Qt .qm translation files -- the app never installs a QTranslator.
    if "/translations/" in norm or norm.startswith("translations/"):
        return True

    # QML modules under PySide6/qml/ -- the app uses QtWidgets, not Qt Quick.
    if "/qml/" in norm or norm.startswith("qml/"):
        return True

    for module in UNUSED_QT_MODULES:
        name = module.lower()
        # PySide6 Python wrapper (QtNetwork.pyd, QtNetwork.abi3.so, ...).
        if f"/{name}." in norm or norm.endswith(f"/{name}"):
            return True
        # Native Qt library (Qt6Network.dll, libQt6Network.so.6, ...).
        if f"qt6{module[2:].lower()}." in norm:
            return True

    for plugin_dir in UNUSED_QT_PLUGIN_DIRS:
        if f"/plugins/{plugin_dir}/" in norm:
            return True

    return False


a = Analysis(
    ["app_entry.py"],
    pathex=[str(SRC_DIR)],
    binaries=[],
    datas=DATAS,
    hiddenimports=HIDDEN_IMPORTS,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=["tkinter", *(f"PySide6.{m}" for m in UNUSED_QT_MODULES)],
    noarchive=False,
)

a.binaries = [b for b in a.binaries if not _is_excluded_qt(b[0])]
a.datas = [d for d in a.datas if not _is_excluded_qt(d[0])]

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
