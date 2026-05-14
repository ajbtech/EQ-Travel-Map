# EverQuest Travel Map

Generate a visual travel map and play summary from your EverQuest character's
log files. Drop in your logs, pick your character, click Generate.

![Sample travel map for Gorrek on Project 1999](docs/sample_map.png)

[![tests](https://github.com/<owner>/everquest-travel-map/actions/workflows/test.yml/badge.svg)](https://github.com/<owner>/everquest-travel-map/actions/workflows/test.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue)](pyproject.toml)

## What it does

Reads your EverQuest log files chronologically and draws every valid
zone-to-zone trip on a map of the world. The colour of each line shows when
in your character's history that trip happened (older trips are drawn on top
so early adventures stay visible). Alongside the map, you get a copyable text
summary of kills, deaths, level-ups, looted coin, and merchant earnings.

The map shown above was generated from the bundled sample log
(`samples/sample_eqlog_Gorrek_P1999Green.txt`), a real Project 1999 character
trimmed down to ~1.3 MB so the project ships with a working first-run example.

---

## For EverQuest players (no Python or terminal needed)

> **Note:** A pre-built `EQTravelMap.exe` is attached to each
> [GitHub release](https://github.com/<owner>/everquest-travel-map/releases).
> Download it from there — there is nothing to install and no terminal
> commands to run.

### Try it on the bundled sample (no logs of your own required)

1. Download `EQTravelMap-vX.Y.Z-windows.zip` from the
   [latest release](https://github.com/<owner>/everquest-travel-map/releases/latest).
2. Right-click → **Extract All…** anywhere on your computer.
3. Open the extracted folder and double-click **`EQTravelMap.exe`**.
4. The form is pre-filled with the bundled `samples/` folder and character
   name `Gorrek`. Click **Generate**.
5. After a few seconds you'll see the map and a summary with the option to
   copy them, save the map elsewhere, or open the output folder in Explorer.

### Use it with your own EverQuest logs

1. In-game, type **`/log on`** once. EverQuest will start writing per-character
   log files into its `Logs` folder.
2. In the app, click **Browse** next to *Log folder* and pick that `Logs`
   folder. Common locations on Windows:
   - `%USERPROFILE%\EverQuest\Logs`
   - `C:\EverQuest\Logs`
   - `C:\Program Files\Sony\EverQuest\Logs`
   - `C:\Program Files (x86)\Sony\EverQuest\Logs`
3. Type your character's name exactly as it appears in the filename
   (`eqlog_<Character>_P1999Green.txt` → enter `<Character>`).
4. Click **Generate**. The longer your log history, the longer the parse
   takes — a multi-year archive can take a couple of minutes.
5. Use **Save Map As…** to keep the rendered PNG anywhere you like, or
   **Open Output Folder** to find the default copy in Explorer.

If anything goes wrong, the app shows a friendly explanation with a
"Show Details" button for the technical message — paste that into a
[bug report](https://github.com/<owner>/everquest-travel-map/issues/new?template=bug_report.md)
and we'll take a look.

---

## For command-line users

If you have Python 3.10+ and prefer running from source:

```powershell
git clone https://github.com/<owner>/everquest-travel-map.git
cd everquest-travel-map
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
```

Launch the desktop GUI:

```powershell
python src\desktop_app.py            # GUI, defaults pre-filled
python src\desktop_app.py Gorrek     # GUI, character name pre-filled
```

Or run the parser directly without the GUI:

```powershell
python src\eq_parser.py Gorrek                          # uses default paths
python src\eq_parser.py Gorrek --log-folder samples     # use bundled sample
python src\eq_parser.py Gorrek --log-folder C:\path\to\logs --output map.png
```

`eq_parser.py` prints the summary to stdout and writes the map PNG to
`--output` (default: `~/everquest_travel_map.png`).

---

## For developers

Full setup, testing, and packaging instructions live in
[CONTRIBUTING.md](CONTRIBUTING.md). The short version:

```powershell
pip install -e ".[dev]"
python -m pytest -q src     # 161 tests
ruff check src && black --check src
pyinstaller --noconfirm --clean EQTravelMap.spec   # build the redistributable
```

Architecture and module conventions are documented in [CLAUDE.md](CLAUDE.md).
Open work and good-first-issue ideas live in [TODO.md](TODO.md).

The codebase splits into a streaming parse layer
(`src/log_parser.py`, `src/line_reader.py`), a rendering layer
(`src/eq_display.py`, `src/map_path.py`, `src/zone_graph.py`), a shared
text-summary layer (`src/summary_formatter.py`), and a PySide6 GUI
(`src/desktop_app.py`, `src/ui/`). Tests are colocated as `src/test_*.py`.

---

## License & acknowledgments

This project is released under the [MIT License](LICENSE).

It links against several third-party libraries that retain their own licenses,
notably **Qt 6** and **PySide6** under LGPL-3.0. Distribution is LGPL-compliant
because the bundle uses PyInstaller's `--onedir` mode (Qt DLLs remain
replaceable). See [LICENSES/README.md](LICENSES/README.md) for the full
attribution list and notes.

EverQuest and the world map artwork are property of Daybreak Game Company.
This is an unofficial fan project with no affiliation to Daybreak or the
Project 1999 team. The bundled `zone_map.png` is a community-made annotated
reference of the classic-era Norrath worlds.

Special thanks to the **Project 1999** community for keeping classic
EverQuest alive and to everyone who has reported issues against this tool.

---

## Roadmap

See [TODO.md](TODO.md) for the maintainer's working notes and
[GitHub Issues](https://github.com/<owner>/everquest-travel-map/issues) for
discussion. Highlights for upcoming versions:

- Better Kunark zone center positions
- Live "follow me" view that updates the map as you play
- Zoom and pan in the desktop view
- Replacing the placeholder pixel-art icon with commissioned art
