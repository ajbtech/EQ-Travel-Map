# EQ Travel Map — Test Coverage Assessment

Audit of the current test suite for adequacy, gaps, and cross-cutting
quality concerns. Read alongside `OSS_READINESS_FINDINGS.md`.

## TL;DR

**178 tests, 1.21 s wall-clock, 90 % line coverage (1085 / 1209
statements)** after the T1–T5 follow-up. Original audit numbers were
163 tests / 0.74 s / 84 %. The pure-logic core (parsers, formatters,
money math, zone graph) is well-covered with named-behavior tests and
consistent TDD discipline. Remaining gaps are concentrated in the
`EngravedHeading` widget (T7) and the bootstrap/exec branches of
`ui/app.py` (T4 partial).

Verdict: **adequate for v0.1.0**, with the most material gaps now
closed. Status of each follow-up is marked inline below.

---

## Coverage at a glance

```
src/eq_list.py                     100%
src/money_sorter.py                100%
src/summary_formatter.py           100%
src/ui/parse_worker.py             100%
src/ui/views/progress_view.py      100%
src/ui/widgets/parchment_panel.py  100%
src/log_parser.py                   98%
src/map_path.py                     98%
src/line_reader.py                  97%
src/zone_graph.py                   95%
src/ui/views/results_view.py        91%
src/ui/views/input_view.py          90%
src/eq_parser.py                    89%
src/eq_display.py                   84%
src/ui/main_window.py               80%
src/ui/widgets/map_canvas.py        73%
src/ui/widgets/engraved_heading.py   0%
src/ui/app.py                        0%
src/ui/asset_paths.py                0%
src/desktop_app.py                   0%
                                   ----
TOTAL                               84%
```

Test counts per module:

```
58  test_line_reader.py
23  test_eq_parser.py
20  test_money_sorter.py
13  test_eq_display.py
10  test_main_window.py
 7  test_zone_graph.py
 7  test_parse_worker.py
 7  test_eq_list.py
 5  test_summary_formatter.py
 5  test_map_path.py
 5  test_log_parser.py
 3  test_input_view.py
```

---

## Should-fix

### T1. No end-to-end test against `samples/sample_eqlog_Gorrek_P1999Green.txt` — ✅ Resolved
- The bundled sample is the documented "first-run experience"
  (`README.md:33-44`, `samples/README.md`), and `CONTRIBUTING.md:26`
  even calls it a CLI smoke-test target. Yet no `test_*.py` references
  `samples/sample_eqlog_Gorrek_P1999Green.txt` (verified by grep).
- Every parser test uses tiny synthetic strings; a regression that
  breaks the real 18,112-line log would not fail CI.
- New `src/test_integration.py` parses the bundled sample and pins
  the headline counts (`line_count==18112`, `login_count==668`,
  `death_count==39`, `zone_count==1086`, `kill_count==5123`,
  `current_level==51`, `loot_cash.platinum==26876`,
  `merch_cash.platinum==9525`) plus asserts that
  `eq_parser.draw_zone_path` produces a valid (>100 KB, PNG header)
  output image. Runs in ~0.6 s and turns the sample into a load-bearing
  CI fixture.

### T2. `_split_error_message` (`src/ui/main_window.py:24-44`) is untested — ✅ Resolved
- This function classifies parse exceptions into friendly user-facing
  strings (`"No log files were found…"`, `"…couldn't read one of the
  log files…"`). Three distinct branches, all driven by substring
  matching against an error message.
- Currently 0 coverage on lines 17-40 (the `_default_error_dialog` +
  `_split_error_message` pair).
- `src/test_main_window.py` gains four new tests covering the missing-log,
  permission-denied, generic-fallback, and empty-input branches via
  direct import of `_split_error_message`.

### T3. `MapCanvas` success path and rescale untested (`src/ui/widgets/map_canvas.py:30-36, 45-50`) — ✅ Resolved
- Existing tests cover the error branches (file missing, null pixmap)
  but never the happy path where a real PNG loads and rescales on
  resize.
- The whole widget is 73 % covered, and the rescale logic is the most
  likely place a user-visible UI bug surfaces (image distortion,
  zero-size pixmap).
- New `src/test_map_canvas.py` adds three tests: pixmap is non-null
  after loading `docs/sample_map.png`, the loaded pixmap respects
  widget bounds (aspect ratio), and resizing a shown widget triggers
  a real rescale (uses `qt_app.processEvents()` to drive the resize
  event through headless Qt). `map_canvas.py` 73 % → 91 %.

### T4. `_load_stylesheet` in `src/ui/app.py` swallows template errors silently — ✅ Resolved
- `ui/app.py` is 0 % covered (no `test_app.py` file exists).
- `_load_stylesheet` does `template.format(stone=…, canvas=…,
  beveled_stone=…)`. If `eq_theme.qss` ever references a fourth
  placeholder the `.format()` raises `KeyError`, crashing app
  startup. That's exactly the failure mode CI should catch.
- New `src/test_app.py` covers `_load_stylesheet` (happy path + the
  no-op-when-theme-missing branch), `build_arg_parser` (positional +
  flag round trip, optional character), and the
  `_infer_character_names` / `_default_character_name` helpers used
  by the GUI to prefill the character field.
- `ui/app.py` 0 % → 67 %; `ui/asset_paths.py` 0 % → 78 %.
  Remaining uncovered chunk in `app.py` is the
  `QApplication.exec()` mainloop (lines 80–95, 99–100, 104), which
  is intentionally out of scope for unit tests.

### T5. No coverage gate in CI — ✅ Resolved
- `.github/workflows/test.yml` runs `pytest` without `coverage`.
- No `[tool.coverage]` config in `pyproject.toml`, no `.coveragerc`.
- The 84 % figure here came from a one-off local run; nothing is
  watching it drift.
- `coverage>=7.0` added to `[project.optional-dependencies].dev` in
  `pyproject.toml`.
- `[tool.coverage.run]` and `[tool.coverage.report]` blocks added to
  `pyproject.toml`. Threshold set to **`fail_under = 85`** (current
  coverage is 90 %, leaving ~5 points of slack for legitimate
  Qt-paint gaps).
- New `coverage` job in `.github/workflows/test.yml` runs on every
  push / PR alongside the existing `test` and `lint` jobs (Linux /
  Python 3.12 / Qt offscreen). `coverage report` is the gate — it
  exits non-zero when the threshold is violated.

---

## Nice-to-have

### T6. `InputView` coverage is shallow (3 tests, 90 % lines)
- `src/test_input_view.py` only exercises the "generate" button
  enable/disable logic. `TODO.md` already flags
  *"Add tests for the UI views (InputView, ProgressView, ResultsView)
  and widgets (MapCanvas, ParchmentPanel, EngravedHeading)"* as a
  good-first-issue.
- Missing: the browse-folder slot, character-name field validation,
  prefill from constructor args, the path-not-a-directory branch.
- ProgressView and ResultsView are at 100 % already (covered
  indirectly via `test_main_window.py`), so the gap is really
  InputView-specific.

### T7. `EngravedHeading` widget at 0 %
- `src/ui/widgets/engraved_heading.py` — 40 statements, no test
  file. `paintEvent` is brittle, three-pass text rendering with
  hardcoded color constants and a custom `sizeHint`.
- Not user-facing-broken if the paint silently no-ops, but it would
  fail a refactor unnoticed.
- A minimal test that instantiates the widget, calls
  `setText("Hello")`, and asserts `sizeHint().width() > 0` would
  catch most regressions.

### T8. `asset_paths.py` at 0 %
- `src/ui/asset_paths.py` — 18 statements, no test file.
- The `_MEIPASS`-vs-source branch is the exact code that decides
  whether the frozen PyInstaller bundle finds its assets. It works
  today, but if `_project_root()` ever drifts (e.g. `parents[2]`
  becomes wrong after a file move) nothing tells you until you
  build the exe.
- Recommended: two tests, one monkeypatching `sys._MEIPASS` and one
  without, asserting `project_asset("icon.ico")` resolves to the
  expected path.

### T9. `MapRenderer` drawing primitives only tested via mocks
- `src/test_eq_parser.py` exercises `draw_zone_path` end-to-end but
  via `monkeypatch.setattr(eq_display, "MapRenderer", FakeRenderer)`
  in most tests. The real `MapRenderer.draw_line`/`draw_dot`/
  `save_map` Pillow code path is only covered by a handful of cases
  (`test_draw_zone_path_can_save_map` etc.) without asserting
  anything about the resulting PNG.
- Already addressed structurally by T1 (an end-to-end test against
  the bundled sample asserting the file is a valid non-empty PNG of
  the expected dimensions).
- Pixel-snapshot testing is overkill here — flaky and CI-platform
  dependent — so skip that.

### T10. `desktop_app.py` is the entry shim and could be smoke-tested
- 0 % coverage on 6 statements (`src/desktop_app.py`).
- A one-line `python -c "import desktop_app"` smoke test in CI would
  catch import-time regressions in the entry shim. Optional.

### T11. Missing branch coverage on minor edge cases
Small uncovered branches the suite could pin down without much effort:
- `src/line_reader.py:116` — `extract_between` end-marker not found
- `src/line_reader.py:152` — `HELP` event classification
- `src/line_reader.py:167` — final `EMPTY_LINE_EVENT` fallback
- `src/log_parser.py:107-108` — `parse_timestamp` `ValueError` branch
- `src/eq_display.py:54` — `MapRenderer` resize when map image is
  the "wrong" size (would surface if `zone_map.png` is ever swapped
  for a different-resolution asset)
- `src/eq_display.py:111` — `make_rainbow` fallback to the last stop
  (only reachable with `percent > 1.0`)

None individually critical; collectively a clean "raise coverage to
≥ 90 %" PR.

---

## Verified clean / strengths

- **Pure-logic core is excellent.** `eq_list`, `money_sorter`, and
  `summary_formatter` are at 100 % with behavior-named tests.
  `log_parser` (98 %) and `line_reader` (97 %) are the meat of the
  app and are very well covered: 58 `test_line_reader` cases alone.
- **Test names communicate behavior.**
  `test_parser_uses_most_recent_level_event_as_current_level`,
  `test_parse_requested_routes_canceled_back_to_input` — readable,
  scoped, ground-truthy. Consistent TDD discipline visible.
- **Fast.** 0.74 s for 163 tests means there's no excuse for skipping
  the suite locally — encourages TDD per `CONTRIBUTING.md`.
- **Qt headless setup is correct.** `conftest.py`'s `qt_app` fixture
  + `QT_QPA_PLATFORM=offscreen` in CI means widget tests are real
  Qt, not mocks. `test_main_window.py` (10 tests) and
  `test_parse_worker.py` (7 tests) exercise signals, slots, and
  view routing.
- **Worker tests are dependency-injected, not patched.**
  `MainWindow` takes a `worker_factory` argument and tests pass a
  fake one. This is the right architecture for testability and
  scales well.
- **All tests passed during this audit.** `163 passed in 0.74s` on
  a fresh venv. `ruff check src` and `black --check src` both clean.

---

## Audit metadata

- Original audit at `f68fa35`; T1–T5 follow-up at HEAD of
  `claude/eq-travel-map-opensource-dQ5GJ` (PR #9).
- Tooling: `coverage==7.x` (line coverage only; branch coverage not
  enabled), `pytest`, manual inspection of every `test_*.py` and every
  uncovered code chunk reported by `coverage report -m`.
- Verification commands (post-T1–T5):
  - `QT_QPA_PLATFORM=offscreen coverage run -m pytest -q src` →
    `178 passed in 1.21s`
  - `coverage report` → `TOTAL 1209 124 90%`, exit 0 (above
    `fail_under = 85` threshold)
  - `ruff check src` and `black --check src` → both clean
- Branch coverage (`coverage run --branch`) was not measured here.
  Worth re-running with `--branch` later; it typically drops a
  line-coverage figure by 5–10 points.
