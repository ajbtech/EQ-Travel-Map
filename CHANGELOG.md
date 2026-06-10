# Changelog

All notable changes to this project are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and this project
adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Changed
- Replaced the random per-visit "jitter" with deterministic colour rings.
  Each zone is now drawn as a filled circle whose colour runs from the
  earliest visit's rainbow colour at the centre to the latest at the edge, so
  a zone visited throughout a character's life reads red→violet from the
  inside out. Zone transitions are drawn as trapezoidal bands beneath the
  circles: each trip's band meets each circle at that trip's colour ring and
  spans its full width, so repeated trips nest outward as the rings grow and
  fill the gap between zones with chronological colour stripes. Each zone's
  circle is also sized by how often it was visited — disc *area*
  is proportional to its visit count relative to the busiest zone, so the
  most-visited zone fills the maximum radius and the rest scale down. The map
  is now fully deterministic (no RNG), so the same log always renders
  identically.

### Added
- "MAKE VIDEO" button on the results window exports an MP4 that replays the
  character's journey: travel lines draw onto the map and the summary stats
  count up over a chosen duration (30 s / 1 min / 2 min / 5 min / custom).
  Frames are captured from the results view itself, so the video matches the
  on-screen style. Generation runs without freezing the UI and can be canceled.

## [1.0.0] - 2026-05-17

First stable release. Rolls up the 0.1.1 → 0.1.14 patch series plus the
metadata bumps that mark the project as production-stable.

### Added
- Remember the last log folder across app launches so the input view
  starts pre-filled on subsequent runs.
- Real progress-bar percentage during log parsing (was previously a
  spinner-style indeterminate bar).
- Saved map filenames are now prefixed with the character name
  (e.g. `Gorrek_travel_map.png`) so multiple characters can coexist in
  the same output folder.

### Changed
- Progress-bar fill colour switched from default blue to gold so it
  matches the EverQuest palette.
- Results window now caps to the active screen size and shrinks
  proportionally on small displays, instead of overflowing.
- Parchment title moved up to free vertical room for body content; the
  stone-framed parchment construction is now shared between the input
  and progress views.
- Button styling updated to better match the original EverQuest UI.

### Fixed
- Coin retrieved from looting your *own* corpse is no longer added to
  loot cash totals (previously inflated platinum/gold for any character
  that died and recovered).
- "Sirens Grotto" log spelling now aliases to the canonical "Siren's
  Grotto" zone so trips into the zone draw correctly on the map.
- ParchmentPanel no longer enforces a minimum height that overrode
  `setFixedSize` on small windows.
- Capitalisation of looted-item names normalised in the summary.

### Internal
- Bundle size reduced via PNG asset compression, stripped unused Qt
  modules / Pillow plugins / stdlib modules, and a swap from matplotlib
  to Pillow as the map renderer.
- `html` stdlib module restored to the PyInstaller bundle (was being
  pruned and broke the frozen exe on certain code paths).
- Test coverage raised to 90 % with a `fail_under = 85` CI gate
  (`pyproject.toml [tool.coverage]`), an end-to-end test against the
  bundled `samples/sample_eqlog_Gorrek_P1999Green.txt`, and new tests
  for `_split_error_message`, `MapCanvas` rescale, and the `ui/app.py`
  stylesheet loader.
- Release artifacts now ship with `SHA256SUMS.txt` and pinned
  dependencies (`requirements-release.txt`) for reproducible builds.

## [0.1.0] - 2026-05-16

First public release.

### Added
- Desktop GUI (PySide6) for non-CLI users: pick a log folder + character name,
  click Generate, see the map and a play summary.
- Command-line entry (`python src/eq_parser.py <Character>`) for power users
  and scripting.
- Streaming log parser that classifies zones, kills, deaths, level changes,
  logins, looted coin, and merchant cash.
- Zone graph (`zone_graph.json`) plus jitter so repeated visits are visible
  on the map without crowding the zone center.
- Bundled sample log (`samples/sample_eqlog_Gorrek_P1999Green.txt`) so new
  users and CI can generate a map without supplying their own logs.
- "Where are my logs?" disclosure, friendly inline validation, and a
  classified error dialog with a Show Details expander on parse failures.
- "Save Map As…" and "Open Output Folder" buttons in the results view.
- 8-bit pixel-art application icon.
- PyInstaller `--onedir` packaging (`EQTravelMap.spec`) producing a
  redistributable Windows zip; LGPL-compliant per Qt's licensing.
- GitHub Actions workflows: tests on Linux + Windows × Python 3.10/3.11/3.12
  with ruff and black lint, plus an automated release workflow that builds
  and uploads the Windows zip on tag push.

[Unreleased]: https://github.com/ajbtech/EQ-Travel-Map/compare/v1.0.0...HEAD
[1.0.0]: https://github.com/ajbtech/EQ-Travel-Map/compare/v0.1.0...v1.0.0
[0.1.0]: https://github.com/ajbtech/EQ-Travel-Map/releases/tag/v0.1.0
