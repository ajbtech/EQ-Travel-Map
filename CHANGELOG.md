# Changelog

All notable changes to this project are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and this project
adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

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

[Unreleased]: https://github.com/ajbtech/EQ-Travel-Map/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/ajbtech/EQ-Travel-Map/releases/tag/v0.1.0
