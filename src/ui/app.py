import argparse
import re
import sys
from pathlib import Path

from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication

import eq_parser
from ui import asset_paths
from ui.main_window import MainWindow

_LOG_CHARACTER_PATTERN = re.compile(r"eqlog_(?P<character>[^_]+)_", re.IGNORECASE)


def _infer_character_names(log_folder_path):
    names = set()
    for log_file in Path(log_folder_path).glob("*eqlog_*_*.txt"):
        match = _LOG_CHARACTER_PATTERN.search(log_file.name)
        if match is not None:
            names.add(match.group("character"))
    return sorted(names, key=str.lower)


def _default_character_name(log_folder_path):
    names = _infer_character_names(log_folder_path)
    return names[0] if len(names) == 1 else ""


def _set_app_icon(app):
    icon_path = asset_paths.project_asset("icon.ico")
    if not icon_path.exists():
        icon_path = asset_paths.project_asset("icon.png")
    if icon_path.exists():
        app.setWindowIcon(QIcon(str(icon_path)))


def _load_stylesheet(app):
    qss_path = asset_paths.theme_dir() / "eq_theme.qss"
    if not qss_path.exists():
        return
    template = qss_path.read_text(encoding="utf-8")
    stylesheet = template.format(
        stone=asset_paths.to_qss_url(
            asset_paths.project_asset("original_eq_stone_texture.png")
        ),
        canvas=asset_paths.to_qss_url(asset_paths.project_asset("eq_canvas.png")),
        beveled_stone=asset_paths.to_qss_url(
            asset_paths.project_asset("beveled_stone_9patch.png")
        ),
    )
    app.setStyleSheet(stylesheet)


def build_arg_parser():
    parser = argparse.ArgumentParser(
        description="Open the EverQuest Travel Map desktop app.",
    )
    parser.add_argument(
        "character_name",
        nargs="?",
        help="Optional character name to prefill in the app.",
    )
    parser.add_argument(
        "--log-folder",
        default=eq_parser.DEFAULT_LOG_FOLDER_PATH,
        type=Path,
        help="Folder containing EverQuest log files.",
    )
    parser.add_argument(
        "--output",
        default=eq_parser.DEFAULT_MAP_OUTPUT_PATH,
        type=Path,
        help="Path where the generated map image should be saved.",
    )
    return parser


def run(character_name=None, log_folder_path=None, output_path=None):
    log_folder_path = Path(log_folder_path or eq_parser.DEFAULT_LOG_FOLDER_PATH)
    output_path = Path(output_path or eq_parser.DEFAULT_MAP_OUTPUT_PATH)
    if character_name is None:
        character_name = _default_character_name(log_folder_path)

    app = QApplication.instance() or QApplication(sys.argv)
    _load_stylesheet(app)
    _set_app_icon(app)

    window = MainWindow(
        default_log_folder=log_folder_path,
        default_output_path=output_path,
        default_character_name=character_name,
    )
    window.show()
    return app.exec()


def main():
    args = build_arg_parser().parse_args()
    sys.exit(run(args.character_name, args.log_folder, args.output))


if __name__ == "__main__":
    main()
