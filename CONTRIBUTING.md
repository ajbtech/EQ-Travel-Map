# Contributing

Thanks for your interest in EverQuest Travel Map! This guide covers the basics
for contributors.

## Dev environment

Requires Python 3.10 or newer.

```powershell
git clone https://github.com/<your-fork>/everquest-travel-map.git
cd everquest-travel-map
python -m venv .venv
.\.venv\Scripts\activate          # Windows
# source .venv/bin/activate         # Linux/macOS
pip install -e ".[dev]"
```

`pip install -e ".[dev]"` pulls in the runtime dependencies (PySide6, Pillow,
matplotlib) plus the dev tools (pytest, ruff, black, pyinstaller).

## Running the app from source

```powershell
python src\desktop_app.py            # GUI
python src\eq_parser.py Gorrek --log-folder samples   # CLI smoke test
```

The bundled `samples/sample_eqlog_Gorrek_P1999Green.txt` is a real log file
trimmed down to ~1.3 MB. It's used by tests and as the first-run experience
for users who haven't generated their own EverQuest logs yet.

## Tests

Always run the full suite before opening a PR:

```powershell
python -m pytest -q src
```

Headless GUI tests use Qt's offscreen platform via `conftest.py`'s `qt_app`
fixture. CI sets `QT_QPA_PLATFORM=offscreen` for the same reason.

### Test-driven development

Per the project convention, **write a failing test first, then implement**.
Tests live in `src/test_*.py` next to the module they cover. A few examples
to crib from:

- `src/test_log_parser.py` — pure-logic tests over tiny in-memory log fixtures
- `src/test_main_window.py` — Qt widget tests using the `qt_app` fixture and
  injected fakes for the parse worker

## Code style

```powershell
python -m ruff check src
python -m black src
```

Both are enforced in CI. `pyproject.toml` pins line length 88, target Python
3.10, ruff rule selection `E F W I`.

## Building the standalone executable

```powershell
pyinstaller --noconfirm --clean EQTravelMap.spec
```

Output lands in `dist/EQTravelMap/`. Smoke-test by running
`dist/EQTravelMap/EQTravelMap.exe` and clicking Generate against the bundled
sample. The released zip is built automatically by
`.github/workflows/release.yml` on tag push (`vX.Y.Z`).

## Project layout

See [CLAUDE.md](CLAUDE.md) for a deeper architectural tour. Quick map:

| Area | What lives there |
| --- | --- |
| `src/log_parser.py`, `src/line_reader.py` | Streaming parse of EverQuest log lines |
| `src/eq_display.py`, `src/map_path.py` | Map rendering and travel-line geometry |
| `src/zone_graph.py`, `zone_graph.json` | Zone adjacency data and queries |
| `src/summary_formatter.py` | Text summary used by both GUI and CLI |
| `src/desktop_app.py`, `src/ui/` | PySide6 desktop app |
| `EQTravelMap.spec`, `app_entry.py` | PyInstaller packaging |

## Good first issues

Look at the [good first issue](https://github.com/<owner>/everquest-travel-map/labels/good%20first%20issue)
label for tickets sized for newcomers. Adding a new EverQuest zone is one of
the simplest:

1. Add the zone to `zone_graph.json` under `nodes` with a `center: [x, y]`
   pixel coordinate, plus its connections under `edges`.
2. Add an alias entry in `zone_graph.json` if the log name differs from the
   map name.

## Pull request flow

1. Fork → branch → commits → PR against `main`.
2. The PR template prompts for a short summary, change list, and a checklist
   covering tests, lint, and personal-data hygiene.
3. CI (tests on Linux + Windows × Python 3.10/3.11/3.12, plus lint) must be
   green before merge.
4. New user-visible behavior should also bump `CHANGELOG.md`.

## Questions

Open a [discussion](https://github.com/<owner>/everquest-travel-map/discussions)
or a low-stakes issue. Thanks for helping!
