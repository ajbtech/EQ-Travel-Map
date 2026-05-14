# Third-party licenses

This application is released under the MIT License (see `../LICENSE`). It links
against the following third-party components, each retaining its own license:

| Component | License | Source |
| --- | --- | --- |
| Qt 6 | LGPL-3.0 | https://download.qt.io/ |
| PySide6 | LGPL-3.0 | https://code.qt.io/cgit/pyside/pyside-setup.git/ |
| Pillow | HPND (MIT-compatible) | https://github.com/python-pillow/Pillow |
| Matplotlib | Matplotlib license (BSD-style) | https://github.com/matplotlib/matplotlib |

## LGPL compliance notes

Qt and PySide6 are LGPL-3.0. Distributing this application under MIT is permitted
because:

- Your own code (in `src/` and `assets/`) is licensed under MIT and is not a
  derivative work of Qt — it merely uses Qt through dynamic linking.
- The full text of the LGPL-3.0 is required to be made available to recipients.
  See `Qt-LGPL-NOTICE.txt` for the canonical link.
- When packaging with PyInstaller, use `--onedir` (not `--onefile`) so the Qt
  DLLs remain replaceable in the bundle. Do not statically link Qt.
- This `LICENSES/` directory should be copied next to the built executable so
  end users receive the notices.
