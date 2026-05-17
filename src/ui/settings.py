"""Persisted user preferences for the desktop app.

Backed by ``QSettings`` so storage location is platform-native (registry on
Windows, plist on macOS, ``~/.config`` on Linux). Tests redirect
``_make_settings`` to an ini file in a temp dir for isolation.
"""

from pathlib import Path

from PySide6.QtCore import QSettings

_ORGANIZATION = "EQ-Travel-Map"
_APPLICATION = "EQ-Travel-Map"
_LOG_FOLDER_KEY = "last_log_folder"


def _make_settings():
    return QSettings(_ORGANIZATION, _APPLICATION)


def load_log_folder():
    value = _make_settings().value(_LOG_FOLDER_KEY)
    if not value:
        return None
    return Path(str(value))


def save_log_folder(folder):
    _make_settings().setValue(_LOG_FOLDER_KEY, str(folder))
