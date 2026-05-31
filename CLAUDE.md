# EverQuest Travel Map

This project generates a visual map of an EverQuest (Project 1999) character's travel history. It reads the game's raw text log file, extracts zone transitions, level-ups, deaths, kills, and cash events, then draws lines between adjacent zones on a map image and produces a text summary.

The primary distribution target is a standalone executable, but the source is open for modification.

## Application flow

The desktop app has two windows:

1. **Input / progress window** — a small window where the user enters a character name and log folder path. Once parsing begins, this same window shows live progress as log files are read.
2. **Results window** — a larger window that opens after parsing completes, displaying the travel map and the aggregated metrics (kills, deaths, levels, cash, etc.).

## Project layout

- `src/eq_parser.py` — command-line entry point
- `src/desktop_app.py` — desktop GUI entry point
- `src/log_parser.py` — streams log files and builds a parsed summary
- `src/line_reader.py` — classifies individual log lines into events
- `src/eq_display.py` — zone center coordinates and map drawing logic
- `src/map_path.py` — converts zone visits into drawable map segments (graph-skip, jitter)
- `src/money_sorter.py` — parses and normalises cash values
- `src/summary_formatter.py` — builds the text summary used by both the CLI and desktop app
- `src/zone_graph.py` — loads `data/zone_graph.json` and checks zone adjacency
- `src/desktop_app.py` and `src/ui/` — PySide6 desktop GUI (entry shim, app, main window, views, widgets)
- `src/ui/theme/eq_theme.qss` — Qt stylesheet that drives the desktop app's visual style
- `tests/` — pytest suite (`test_*.py`) and shared `conftest.py`
- `data/zone_graph.json` — zone nodes, aliases, and valid connections
- `data/zone_map.png` — base map image used by the renderer

## Running the app

```powershell
python src\desktop_app.py
python src\desktop_app.py Gorrek        # prefill character name
python src\eq_parser.py Gorrek          # command-line only
```

Log files must be in the project root and match `*eqlog_<CharacterName>_*.txt`.

## Running tests

```powershell
python -m pytest -q tests
```

## Development practice

**Use test-driven development for all new behavior.** Write a failing test first, then implement until it passes. Tests live in `tests/test_*.py`, one file per module under test.

**Before committing, always run `ruff check src tests` and `black src tests` and fix any issues first.**

**Prefer a single return statement per function.** Use a single exit point rather than multiple `return`s where practical.

**Keep individual lines simple.** Avoid dense one-liners; extract conditions into named variables (e.g. `is_quoted_chat = ...`) instead of packing multiple checks into one expression.

## TODO tracking

Open work items live in `TODO.md`, grouped under Bugs / Features / Polish / Deferred. When you finish a task, check `TODO.md` for related items and tick them off. When the user defers something mid-conversation ("not now", "later", "next time"), append it to the relevant section rather than relying on memory.

## Adding a new zone

1. Add the zone to `data/zone_graph.json` under `nodes` with a `center: [x, y]` pixel coordinate, plus its connections under `edges`.
2. Add an alias entry in `data/zone_graph.json` if the log name differs from the map name.
