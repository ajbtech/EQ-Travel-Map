# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec for the EverQuest Travel Map desktop app.

Build with: ``pyinstaller EQTravelMap.spec`` from the repo root.

Mode: ``--onedir`` (required by Qt LGPL terms -- see ``LICENSES/README.md``).
The resulting ``dist/EQTravelMap/`` folder is what gets zipped and attached to
GitHub Releases for download by non-CLI users.
"""

import os
import sys
from pathlib import Path

from PyInstaller.utils.hooks import collect_data_files, copy_metadata


PROJECT_ROOT = Path(SPECPATH).resolve()
SRC_DIR = PROJECT_ROOT / "src"

# imageio-ffmpeg ships the ffmpeg binary the video exporter shells out to;
# it must be bundled or video generation fails on machines without ffmpeg.
IMAGEIO_FFMPEG_DATAS = collect_data_files("imageio_ffmpeg")

# imageio calls importlib.metadata.version("imageio") on import; without the
# .dist-info folder in the bundle that raises PackageNotFoundError at runtime.
IMAGEIO_METADATA = copy_metadata("imageio")

# (source on disk, target directory inside the bundle)
# ``samples/`` is intentionally not bundled here -- it ships as a separate
# ``EQTravelMap-samples.zip`` release asset to keep the Windows download
# small for users who already have their own log files.
DATAS = [
    (str(PROJECT_ROOT / "assets"), "assets"),
    (str(PROJECT_ROOT / "LICENSES"), "LICENSES"),
    (str(SRC_DIR / "ui" / "theme"), "ui/theme"),
    (str(PROJECT_ROOT / "zone_graph.json"), "."),
    (str(PROJECT_ROOT / "zone_map.png"), "."),
] + IMAGEIO_FFMPEG_DATAS + IMAGEIO_METADATA

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
    "video_generator",
    "zone_graph",
    "ui.app",
    "ui.asset_paths",
    "ui.main_window",
    "ui.parse_worker",
    "ui.video_worker",
    "ui.views.input_view",
    "ui.views.progress_view",
    "ui.views.results_view",
    "ui.widgets.engraved_heading",
    "ui.widgets.map_canvas",
    "ui.widgets.parchment_panel",
    "imageio",
    "imageio_ffmpeg",
    "numpy",
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

# Qt developer tools shipped inside PySide6/ -- linguist, designer, the
# QML toolchain, uic/rcc, etc. The runtime app never invokes them.
UNUSED_QT_TOOL_EXES = [
    "assistant", "designer", "linguist",
    "lupdate", "lrelease", "uic", "rcc",
    "qmllint", "qmlformat", "qmlimportscanner", "qmlcachegen",
    "qmlplugindump", "qmlpreview", "qmlprofiler",
    "qmlscene", "qmltestrunner", "qmltime",
    "balsam", "balsamui",
]

# matplotlib used to be a runtime dependency (it drove the map renderer).
# The renderer was rewritten on top of Pillow, so list it here as a
# defensive PyInstaller exclude -- if a stray ``import matplotlib`` ever
# sneaks back into the codebase, the bundle will fail loudly at runtime
# instead of silently re-bundling ~25 MB of dead code. numpy is NOT excluded:
# the video exporter (ui.video_worker) uses it to move pixels between Pillow,
# Qt, and imageio.
UNUSED_HEAVY_DEPS = ["matplotlib"]

# Pillow image-format plugins. Pillow auto-registers every plugin it can
# import, but the app only ever opens PNG (the bundled assets and the
# user-supplied zone_map.png). Keep PngImagePlugin; drop the rest.
UNUSED_PIL_PLUGINS = [
    "PIL.BlpImagePlugin", "PIL.BmpImagePlugin", "PIL.BufrStubImagePlugin",
    "PIL.CurImagePlugin", "PIL.DcxImagePlugin", "PIL.DdsImagePlugin",
    "PIL.EpsImagePlugin", "PIL.FitsImagePlugin", "PIL.FliImagePlugin",
    "PIL.FpxImagePlugin", "PIL.FtexImagePlugin",
    "PIL.GbrImagePlugin", "PIL.GifImagePlugin", "PIL.GribStubImagePlugin",
    "PIL.Hdf5StubImagePlugin",
    "PIL.IcnsImagePlugin", "PIL.IcoImagePlugin", "PIL.ImImagePlugin",
    "PIL.ImtImagePlugin", "PIL.IptcImagePlugin",
    "PIL.Jpeg2KImagePlugin", "PIL.JpegImagePlugin",
    "PIL.McIdasImagePlugin", "PIL.MicImagePlugin", "PIL.MpegImagePlugin",
    "PIL.MpoImagePlugin", "PIL.MspImagePlugin",
    "PIL.PalmImagePlugin", "PIL.PcdImagePlugin", "PIL.PcxImagePlugin",
    "PIL.PdfImagePlugin", "PIL.PixarImagePlugin", "PIL.PpmImagePlugin",
    "PIL.PsdImagePlugin", "PIL.QoiImagePlugin",
    "PIL.SgiImagePlugin", "PIL.SpiderImagePlugin", "PIL.SunImagePlugin",
    "PIL.TgaImagePlugin", "PIL.TiffImagePlugin",
    "PIL.WebPImagePlugin", "PIL.WmfImagePlugin",
    "PIL.XbmImagePlugin", "PIL.XpmImagePlugin", "PIL.XVThumbImagePlugin",
]

# Native libraries shipped with Pillow for image formats we don't read or
# write. matplotlib is gone now, but Pillow itself still uses lcms2 for the
# PNG color pipeline; freetype is only used by ImageFont/text rendering and
# the app no longer renders text via Pillow, so freetype could in principle
# be excluded too -- left in for safety in case a Qt code path pulls it.
UNUSED_PIL_NATIVE_LIB_STEMS = [
    "libtiff", "libwebp", "libwebpdemux", "libwebpmux",
    "libjpeg", "libturbojpeg", "libopenjp2", "libjp2",
]

# Pillow C extension modules the app does not call. After the matplotlib
# removal and the metrics-panel removal, the app only uses Image.open,
# Image.new, Image.paste, ImageDraw.line, ImageDraw.ellipse, and Image.save.
# Every other compiled extension Pillow ships is dead weight.
UNUSED_PIL_C_EXTENSION_STEMS = [
    "_imagingft",     # FreeType bindings; used by ImageFont / ImageDraw.text
    "_imagingtk",     # Tkinter integration
    "_imagingmorph",  # Morphology ops (erode, dilate, ...)
    "_avif",          # AVIF format
    "_webp",          # WebP format (C extension; Python plugin already excluded)
]

# Standard-library packages PyInstaller bundles by default but that this
# pure-desktop, no-network, no-database app never imports. Trimming these
# shrinks the PYZ archive and the unpacked .pyc cache. Excluded here rather
# than via a binary/data filter because they are pure-Python packages.
UNUSED_STDLIB_MODULES = [
    "asyncio",
    # "email" is needed by imageio → importlib.metadata (package METADATA files
    # are RFC 822 / email-header format); removing it breaks video export.
    # "html" is imported by src/ui/views/results_view.py for html.escape
    # when building the Qt summary widget -- do NOT add it back.
    "http",
    "xml", "xmlrpc",
    "urllib.request", "urllib.response", "urllib.error", "urllib.robotparser",
    "sqlite3", "_sqlite3",
    "pydoc", "pydoc_data",
    "distutils",
    "lib2to3",
    "ensurepip",
    "idlelib",
    "turtle", "turtledemo",
    "test",
    "unittest",
    "doctest",
    "wsgiref",
    "dbm",
    "curses",
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

    # Qt class metadata for QML / runtime reflection (~15 MB of JSON). A
    # pure-QtWidgets app does not load any of it.
    if "/metatypes/" in norm and norm.endswith("_metatypes.json"):
        return True

    # PySide6 Qt resources -- after excluding the WebEngine module above,
    # this folder only contains its leftover assets (qtwebengine_*.pak,
    # v8_context_snapshot.bin, the WebEngine-specific icudtl.dat). None
    # are needed by a QtWidgets-only app. Matched specifically rather
    # than by /resources/ alone so a hypothetical Qt resource we DO need
    # would not be caught accidentally.
    base = norm.rsplit("/", 1)[-1]
    if "/resources/" in norm and (
        base.startswith("qtwebengine_")
        or base == "icudtl.dat"
        or base == "v8_context_snapshot.bin"
    ):
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

    # PySide6 developer tools (linguist.exe, qmlcachegen.exe, ...). Match
    # both the bare executable and the ``pyside6-<tool>`` wrappers, on
    # Windows (.exe) and POSIX (no extension).
    for tool in UNUSED_QT_TOOL_EXES:
        base = norm.rsplit("/", 1)[-1]
        if base in {tool, f"{tool}.exe", f"pyside6-{tool}", f"pyside6-{tool}.exe"}:
            return True

    return False


def _is_excluded_pillow_lib(dest: str) -> bool:
    """Return True if a bundled entry is a Pillow native lib for an unused format."""
    base = dest.replace("\\", "/").rsplit("/", 1)[-1].lower()

    for stem in UNUSED_PIL_NATIVE_LIB_STEMS:
        # Matches libtiff.dll, libtiff-5.dll, libtiff.so.6, libtiff.6.dylib, ...
        if base.startswith(stem) and (
            base.endswith(".dll") or ".so" in base or base.endswith(".dylib")
        ):
            return True

    return False


def _is_excluded_pillow_ext(dest: str) -> bool:
    """Return True if a bundled entry is an unused Pillow C extension module."""
    norm = dest.replace("\\", "/").lower()
    # Only match inside the PIL package so a similarly named module elsewhere
    # would not be caught.
    if "/pil/" not in norm and not norm.startswith("pil/"):
        return False
    base = norm.rsplit("/", 1)[-1]
    for stem in UNUSED_PIL_C_EXTENSION_STEMS:
        # Matches _imagingft.cp312-win_amd64.pyd, _imagingft.abi3.so, etc.
        if base.startswith(stem) and (base.endswith(".pyd") or ".so" in base):
            return True
    return False


def _keep(entry) -> bool:
    dest = entry[0]
    return not (
        _is_excluded_qt(dest)
        or _is_excluded_pillow_lib(dest)
        or _is_excluded_pillow_ext(dest)
    )


a = Analysis(
    ["app_entry.py"],
    pathex=[str(SRC_DIR)],
    binaries=[],
    datas=DATAS,
    hiddenimports=HIDDEN_IMPORTS,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        "tkinter",
        *(f"PySide6.{m}" for m in UNUSED_QT_MODULES),
        *UNUSED_HEAVY_DEPS,
        *UNUSED_PIL_PLUGINS,
        *UNUSED_STDLIB_MODULES,
    ],
    noarchive=False,
)

a.binaries = [b for b in a.binaries if _keep(b)]
a.datas = [d for d in a.datas if _keep(d)]

pyz = PYZ(a.pure)

if sys.platform == "win32":
    _icon = str(PROJECT_ROOT / "assets" / "icon.ico")
    _codesign_identity = None
    _entitlements_file = None
elif sys.platform == "darwin":
    _icon = str(PROJECT_ROOT / "assets" / "icon.icns")
    _codesign_identity = os.environ.get("CODESIGN_IDENTITY", "-")
    _entitlements_file = None
else:
    _icon = str(PROJECT_ROOT / "assets" / "icon.png")
    _codesign_identity = None
    _entitlements_file = None

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
    codesign_identity=_codesign_identity,
    entitlements_file=_entitlements_file,
    icon=_icon,
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

if sys.platform == "darwin":
    app = BUNDLE(
        coll,
        name="EQTravelMap.app",
        icon=_icon,
        bundle_identifier="com.ajbtech.EQTravelMap",
    )
