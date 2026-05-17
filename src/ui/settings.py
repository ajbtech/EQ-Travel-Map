"""Persisted user preferences for the desktop app.

Backed by ``QSettings`` so storage location is platform-native (registry on
Windows, plist on macOS, ``~/.config`` on Linux). Tests redirect
``_make_settings`` to an ini file in a temp dir for isolation.
"""

import json
from pathlib import Path

from PySide6.QtCore import QSettings

import summary_formatter

_ORGANIZATION = "EQ-Travel-Map"
_APPLICATION = "EQ-Travel-Map"
_LOG_FOLDER_KEY = "last_log_folder"
_LAST_CHARACTER_KEY = "last_character_name"
_LAST_IMAGE_PATH_KEY = "last_map_image_path"
_LAST_SUMMARY_SECTIONS_KEY = "last_summary_sections_json"


def _make_settings():
    return QSettings(_ORGANIZATION, _APPLICATION)


def load_log_folder():
    value = _make_settings().value(_LOG_FOLDER_KEY)
    if not value:
        return None
    return Path(str(value))


def save_log_folder(folder):
    _make_settings().setValue(_LOG_FOLDER_KEY, str(folder))


def save_last_results(character_name, image_path, sections):
    s = _make_settings()
    s.setValue(_LAST_CHARACTER_KEY, str(character_name))
    s.setValue(_LAST_IMAGE_PATH_KEY, str(image_path))
    s.setValue(
        _LAST_SUMMARY_SECTIONS_KEY,
        json.dumps(
            {
                "character_line": sections.character_line,
                "top_kills_lines": list(sections.top_kills_lines),
                "top_zones_lines": list(sections.top_zones_lines),
                "stats_lines": list(sections.stats_lines),
            }
        ),
    )


def load_last_results():
    s = _make_settings()
    character = s.value(_LAST_CHARACTER_KEY)
    image_value = s.value(_LAST_IMAGE_PATH_KEY)
    sections_json = s.value(_LAST_SUMMARY_SECTIONS_KEY)
    if not character or not image_value or not sections_json:
        return None
    image_path = Path(str(image_value))
    if not image_path.exists():
        clear_last_results()
        return None
    try:
        data = json.loads(str(sections_json))
    except (ValueError, TypeError):
        clear_last_results()
        return None
    sections = summary_formatter.SummarySections(
        character_line=data.get("character_line", ""),
        top_kills_lines=list(data.get("top_kills_lines", [])),
        top_zones_lines=list(data.get("top_zones_lines", [])),
        stats_lines=list(data.get("stats_lines", [])),
    )
    return str(character), image_path, sections


def clear_last_results():
    s = _make_settings()
    s.remove(_LAST_CHARACTER_KEY)
    s.remove(_LAST_IMAGE_PATH_KEY)
    s.remove(_LAST_SUMMARY_SECTIONS_KEY)
