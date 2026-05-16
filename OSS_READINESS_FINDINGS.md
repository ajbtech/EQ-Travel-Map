# EQ Travel Map — Open Source Readiness Findings

Audit against the plan in
`/root/.claude/plans/please-make-that-a-foamy-fern.md`. **Resolution
status added in a follow-up pass** — see the ✅ / ⏭️ markers under each
item.

Severity: **Blocker** must fix before going public, **Should-fix**
strongly recommended, **Nice-to-have** polish, **Verified clean**
audited and good.

---

## Blockers

None.

---

## Should-fix

### S1. Unresolved placeholders in `CHANGELOG.md` and `CONTRIBUTING.md` — ✅ Resolved
- `CHANGELOG.md:9` — `## [0.1.0] - TBD` → dated `2026-05-16`.
- `CHANGELOG.md:34-35` — `<owner>/everquest-travel-map` → `ajbtech/EQ-Travel-Map`.
- `CONTRIBUTING.md:11` — clone URL updated to `EQ-Travel-Map`.
- `CONTRIBUTING.md:90` — good-first-issue link updated.
- `CONTRIBUTING.md:110` — discussions link updated.

### S2. Repo slug inconsistency — ✅ Resolved
- All GitHub URLs in CHANGELOG and CONTRIBUTING now use the real repo
  slug `ajbtech/EQ-Travel-Map`. PyPI package name in `pyproject.toml`
  remains `everquest-travel-map` (PyPI-style, intentional).

### S3. `LICENSES/README.md` lists Matplotlib but it's not a dep — ✅ Resolved
- Matplotlib row removed from `LICENSES/README.md`.
- `CONTRIBUTING.md:20` no longer mentions matplotlib in the runtime
  dependency list.
- `LICENSES/README.md` now also points at `assets/ATTRIBUTION.md` for
  image-asset provenance.

### S4. Asset provenance is vague — ✅ Resolved
- New `assets/ATTRIBUTION.md` documents every bundled image with
  origin, credit, and license posture.
- `zone_map.png` credit: *Project 1999 Unofficial Zone Connection Map,
  originally created by Yurz Truly of the Project 1999 server and
  later expanded by Matthew Gordon Roulston (a.k.a Within Amnesia),*
  sourced from https://wiki.project1999.com/Zone_Connection_World.
- `original_eq_*` textures documented as EverQuest UI-derived,
  Daybreak copyright, fan-project posture.
- `README.md:138-144` updated to name the zone map authors inline and
  link to the wiki + the new ATTRIBUTION file.

### S5. Missing `CODE_OF_CONDUCT.md` and `SECURITY.md` — ✅ Resolved
- `CODE_OF_CONDUCT.md` — Contributor Covenant 2.1 drop-in.
- `SECURITY.md` — describes scope (local desktop tool, no network
  surface), routes reports through GitHub Private Vulnerability
  Reporting, lists in-scope vs. out-of-scope.

### S6. README test count is out of date — ✅ Resolved
- `README.md:112` — `# 161 tests` comment dropped from the
  command (counts drift on every PR; the badge already covers it).

---

## Nice-to-have

### N1. Dependency versions are floored, not pinned — ✅ Resolved
- New `requirements-release.txt` pins
  `pyside6==6.11.1`, `shiboken6==6.11.1`, `pillow==12.2.0`,
  `pyinstaller==6.16.0` for the release build.
- `.github/workflows/release.yml` now installs from
  `requirements-release.txt` instead of the floored `requirements.txt`.
- Developer `requirements.txt` keeps the loose `>=` ranges.

### N2. `requirements.txt` and `pyproject.toml` slightly out of sync — ✅ Resolved
- `pytest` removed from `requirements.txt` (it lives correctly in
  `pyproject.toml` `[project.optional-dependencies].dev`).
- `.github/workflows/test.yml` updated to `pip install pytest`
  explicitly after `requirements.txt` so CI still installs it.

### N3. Author email is in every commit on `main` — ⏭️ Skipped
- Informational; no action requested. Standard for OSS work.

### N4. Release artifacts have no checksum / signature — ✅ Resolved
- `.github/workflows/release.yml` now generates `SHA256SUMS.txt`
  alongside the bundle and samples zip and attaches all three to the
  GitHub Release.

### N5. `docs/sample_map.png` is committed at 800 KB — ✅ Resolved
- Re-exported at 1600×919 RGB (was 2700×1550 RGBA): 817 KB → 490 KB,
  saving ~40 %. Still legible inline in the README.

### N6. Deleted-but-still-in-history DejaVu fonts — ⏭️ Skipped
- DejaVu is free; history rewrite isn't worth it for ~250 KB of
  unreachable blobs.

---

## Verified clean (unchanged from original audit)

These were audited per the plan and found to be in good shape; the
maintainer can confidently skip re-checking them.

- **License correctness.** `LICENSE` is a valid MIT license, ©2026 Alex
  Burtness; `pyproject.toml:7` references it. `LICENSES/README.md` and
  `LICENSES/Qt-LGPL-NOTICE.txt` correctly cover Qt 6 / PySide6 LGPL-3.0
  obligations and call out the `--onedir` build mode.
- **LGPL `--onedir` claim.** `EQTravelMap.spec:6` documents `--onedir`,
  the `coll = COLLECT(...)` block at line 264 produces a directory bundle
  (not `--onefile`), and the workflow zips `dist/EQTravelMap/*` — all
  consistent.
- **Trademark / fan-project disclaimer.** `README.md:138-144` clearly
  names Daybreak and Project 1999, states no affiliation, and credits
  the community.
- **Secrets scan.** No verified secrets via `detect-secrets scan`. No
  hardcoded `C:\Users\*`, `/Users/*`, or non-runner `/home/*` paths
  anywhere in the tree. `EQTravelMap.spec:14` uses dynamic
  `Path(SPECPATH)`, `app_entry.py:13-17` uses dynamic relative
  resolution.
- **Sample log PII.** `samples/sample_eqlog_Gorrek_P1999Green.txt`
  (18,112 lines) contains zero `tells`, `says`, `shouts`, `auctions`,
  `OOC`, or chat patterns. No non-Gorrek capitalized speaker names.
- **PNG metadata.** All bundled PNGs have no `tEXt`/`iTXt`/`zTXt`
  chunks. No software/author/copyright strings leaking.
- **`.gitignore` coverage.** Covers `__pycache__/`, venvs, IDE dirs,
  `build/`, `dist/`, `.claude/`, `eqlog_*.txt` (with the
  `!samples/sample_eqlog_*.txt` exception), and scratch artifacts.
- **CI workflows.** `test.yml` matrix is Linux + Windows × Python
  3.10/3.11/3.12, sets `QT_QPA_PLATFORM=offscreen`, runs pytest +
  ruff + black. `release.yml` is tag-triggered, windows-latest,
  references only `GITHUB_TOKEN` (granted via `permissions: contents:
  write`).
- **Issue & PR templates.** Suitable for a public audience.
- **Tests pass on a fresh checkout.** `163 passed in 0.56s` after the
  Should-fix / Nice-to-have edits.
- **Lint clean.** `ruff check src` → all checks passed.
  `black --check src` → "36 files would be left unchanged."
- **End-to-end smoke test.** CLI parser against the bundled sample
  produces a coherent summary and a 703 KB PNG.

---

## Audit metadata

- Repo state at first audit: HEAD `00b67f5`, 20 commits, branch
  `claude/eq-travel-map-opensource-dQ5GJ`.
- Tooling: `detect-secrets`, `git grep` / `git log` across all refs,
  custom Python PNG-chunk parser, `pytest`, `ruff`, `black`, `Pillow`
  (for image re-export).
- Verification after fixes:
  - `QT_QPA_PLATFORM=offscreen python -m pytest -q src` → **163 passed**
  - `ruff check src` → clean
  - `black --check src` → clean
