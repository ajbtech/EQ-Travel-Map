# EQ Travel Map — Open Source Readiness Findings

Audit-only review against the plan in
`/root/.claude/plans/please-make-that-a-foamy-fern.md`. No code or config
was modified. Each finding cites a file path (and line where applicable),
the evidence, and a one-line rationale. Severity: **Blocker** must fix
before going public, **Should-fix** strongly recommended, **Nice-to-have**
polish, **Verified clean** audited and good.

---

## Blockers

None. The repo can go public as-is without exposing secrets, license
violations, or PII. The items below are quality issues a first-time
visitor will notice immediately, so the maintainer may want to treat one
or two of them as effective blockers.

---

## Should-fix (recommended before v0.1.0)

### S1. Unresolved placeholders in `CHANGELOG.md` and `CONTRIBUTING.md`
- `CHANGELOG.md:9` — `## [0.1.0] - TBD` (release date not filled in).
- `CHANGELOG.md:34` — `https://github.com/<owner>/everquest-travel-map/compare/v0.1.0...HEAD`.
- `CHANGELOG.md:35` — `https://github.com/<owner>/everquest-travel-map/releases/tag/v0.1.0`.
- `CONTRIBUTING.md:11` — `git clone https://github.com/<your-fork>/everquest-travel-map.git`.
- `CONTRIBUTING.md:90` — `https://github.com/<owner>/everquest-travel-map/labels/good%20first%20issue`.
- `CONTRIBUTING.md:110` — `https://github.com/<owner>/everquest-travel-map/discussions`.

These render as literal `<owner>` / `<your-fork>` in GitHub's Markdown
view and click through to 404s. The repo is `ajbtech/EQ-Travel-Map`
(per `README.md`), not `everquest-travel-map` — the slug is also wrong.

### S2. Repo slug inconsistency
- `pyproject.toml:2` — `name = "everquest-travel-map"` (Python package name).
- README and actual GitHub repo: `ajbtech/EQ-Travel-Map`.

Two different names are OK (PyPI vs GitHub) but the broken CHANGELOG /
CONTRIBUTING links above all use the package slug as if it were the repo
slug. Decide which one is canonical for URLs and fix the placeholders to
match.

### S3. `LICENSES/README.md` lists Matplotlib, but it's not a dependency
- `LICENSES/README.md:11` — row for "Matplotlib | Matplotlib license (BSD-style)".
- `requirements.txt` and `pyproject.toml` no longer declare matplotlib;
  `EQTravelMap.spec:132` explicitly *excludes* it as a defensive measure
  (renderer was rewritten on Pillow per the comment there).
- `CONTRIBUTING.md:20` also still says `pip install -e ".[dev]"` "pulls
  in the runtime dependencies (PySide6, Pillow, matplotlib)".

Either delete the Matplotlib row (and the CONTRIBUTING mention) or
re-add the dep if something still needs it. Carrying a license notice
for a library you don't ship is harmless but confusing.

### S4. Asset provenance is vague
- `README.md:138-141` describes `zone_map.png` as "community-made" with
  no individual artist or source URL.
- `assets/` contains seven images with no per-file ATTRIBUTION/NOTICE:
  `icon.ico`, `icon.png`, `beveled_stone_9patch.png`, `eq_canvas.png`,
  `original_eq_arrow_left.png`, `original_eq_arrow_right.png`,
  `original_eq_stone_texture.png`. The `original_eq_*` prefix strongly
  implies they're derived from EverQuest UI textures.
- `zone_graph.json:1340` — `"source": "zone_map.png"` (circular, only
  asserts the graph was derived from the bundled image, not where the
  image itself came from).
- PNG metadata in all eight images is empty (checked tEXt/iTXt/zTXt
  chunks) so there's no embedded attribution to harvest.

This is the single biggest legal exposure for a fan project. EverQuest
trademark/copyright belongs to Daybreak, and the README disclaimer
correctly says so, but a DMCA-grade request will still ask "who made
this image?" Recommended: add `assets/ATTRIBUTION.md` (or extend
`LICENSES/README.md`) with — per file — origin, who created/modified
it, and the license under which you can redistribute it. For the
`original_eq_*` assets in particular, document that they are derivative
of EverQuest UI assets under fair-use / fan-project posture and accept
the risk in writing.

### S5. Missing `CODE_OF_CONDUCT.md` and `SECURITY.md`
- `.github/` contains `PULL_REQUEST_TEMPLATE.md` and `ISSUE_TEMPLATE/`
  only. No code of conduct, no security policy.

Not strictly required, but GitHub surfaces both as "Community Standards"
checklist items, and absence is noticeable for a project with a public
issues board. Contributor Covenant is the standard CoC drop-in.

### S6. README test count is out of date
- `README.md:112` — `python -m pytest -q src     # 161 tests`.
- Actual count on a clean run: **163 tests** (`163 passed in 0.58s`).

Either update the comment or remove the count (which goes stale every
PR anyway).

---

## Nice-to-have

### N1. Dependency versions are floored, not pinned
- `requirements.txt` and `pyproject.toml` use `>=` for all deps
  (`pyside6>=6.6`, `pillow>=9.0`, `pytest>=7.0`).

Fine for a library, riskier for a desktop app whose release pipeline
must build a reproducible Windows exe. A future PySide6 6.x release can
break the bundle without any change in this repo. Consider pinning the
release workflow's deps (e.g. a `requirements-release.txt` with `==`)
without changing developer-facing files.

### N2. `requirements.txt` and `pyproject.toml` are slightly out of sync
- `requirements.txt` includes `pytest>=7.0` (a dev-only tool).
- `pyproject.toml` correctly puts pytest under
  `[project.optional-dependencies].dev`.

Either drop pytest from `requirements.txt` or document that
`requirements.txt` is the "everything-to-run-tests" file. Right now a
fresh contributor following the README (`pip install -r
requirements.txt`) gets pytest but not ruff/black/pyinstaller, which is
a confusing middle ground.

### N3. Author email is in every commit on `main`
- `git log --all --pretty=format:'%ae' | sort -u` →
  `alexjburtness@gmail.com` (plus `noreply@anthropic.com` for
  Claude-authored commits).

Standard for OSS work and the maintainer's GitHub handle is already
public, so this is purely informational — flagging because the audit
explicitly looked for emails. No action needed unless you'd rather use
a noreply alias going forward.

### N4. Release artifacts have no checksum / signature
- `.github/workflows/release.yml:48-50` uploads `EQTravelMap-vX-windows.zip`
  and `EQTravelMap-samples.zip` to GitHub Releases without a
  `SHA256SUMS` file or signature.

Users running an unsigned Windows `.exe` already get a SmartScreen
warning. Publishing a `SHA256SUMS.txt` alongside the bundle is a cheap
trust signal and a few extra lines of PowerShell in the workflow.

### N5. `docs/sample_map.png` is committed at 800 KB
- `docs/sample_map.png` — 817 KB, 2700×1550 RGBA.

It's just a single README screenshot. A re-export at smaller dimensions
(e.g. 1600px wide, RGB) would cut repo size meaningfully. Optional.

### N6. Deleted-but-still-in-history `assets/fonts/DejaVuSans*.ttf`
- `git log --diff-filter=D` shows
  `assets/fonts/DejaVuSansMono-Bold.ttf` and `…DejaVuSansMono.ttf`
  removed from the tree but blobs still reachable in history.

DejaVu is under the Bitstream Vera / DejaVu Fonts License (free,
redistributable), so this is not a legal issue, just bloat. No action
needed unless you do a history rewrite for other reasons.

---

## Verified clean

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
  the community. Wording is sufficient for a fan project.
- **Secrets scan.** No verified secrets via `detect-secrets scan`
  (gitleaks/trufflehog not available in this environment, but
  detect-secrets covers the common patterns). No hardcoded
  `C:\Users\*`, `/Users/*`, or non-runner `/home/*` paths anywhere in
  the tree. `EQTravelMap.spec:14` uses dynamic `Path(SPECPATH)`,
  `app_entry.py:13-17` uses dynamic relative resolution.
- **Sample log PII.** `samples/sample_eqlog_Gorrek_P1999Green.txt`
  (18,112 lines) contains zero `tells`, `says`, `shouts`, `auctions`,
  `OOC`, or chat patterns of any kind. No non-Gorrek capitalized speaker
  names appear. NPC merchant names (e.g. "Rezslog") and zone names are
  the only proper nouns. `samples/README.md` documents the trimming
  policy and confirms inclusion with permission.
- **PNG metadata.** All eight bundled PNGs (`zone_map.png`,
  `docs/sample_map.png`, six `assets/*.png`) have no `tEXt`, `iTXt`, or
  `zTXt` chunks. No software/author/copyright strings leaking.
- **`.gitignore` coverage.** Covers `__pycache__/`, venvs, IDE dirs,
  `build/`, `dist/`, `.claude/`, `eqlog_*.txt` (with the
  `!samples/sample_eqlog_*.txt` exception), and scratch artifacts.
- **CI workflows.**
  - `.github/workflows/test.yml` — Linux + Windows × Python 3.10/3.11/3.12
    matrix, installs Linux Qt runtime deps, sets `QT_QPA_PLATFORM=offscreen`,
    runs `pytest` + `ruff check` + `black --check`. References only
    `GITHUB_TOKEN` implicitly.
  - `.github/workflows/release.yml` — tag-triggered, windows-latest,
    builds PyInstaller bundle, zips it and the samples, attaches both
    to a GitHub Release via `softprops/action-gh-release@v2`. No
    custom secrets beyond `GITHUB_TOKEN` (granted via
    `permissions: contents: write`). Correctly aligned with what the
    README promises users will download.
- **Issue & PR templates.** `bug_report.md` asks for scrubbed log
  snippets, `feature_request.md` is generic-but-fine,
  `PULL_REQUEST_TEMPLATE.md` includes a personal-data checklist line.
  All suitable for a public audience.
- **Tests pass on a fresh checkout.** Fresh venv, `pip install -r
  requirements.txt`, `QT_QPA_PLATFORM=offscreen python -m pytest -q
  src` → `163 passed in 0.58s`.
- **Lint clean.** `ruff check src` → all checks passed.
  `black --check src` → "36 files would be left unchanged." First
  public PR's CI will not embarrass the project.
- **End-to-end smoke test.** `python src/eq_parser.py Gorrek
  --log-folder samples --output /tmp/eqtm-out.png` produces a 703 KB
  PNG and prints a coherent summary (1,086 zones, 5,123 kills,
  26,876p looted coin, etc.). The "first-run experience" promised in
  the README actually works.
- **No stray hardcoded paths or debug prints** beyond two intentional
  CLI `print()` calls in `src/eq_parser.py` (user-facing) and one in
  `src/summary_formatter.py:74` inside `print_summary()` which is the
  documented CLI output function.
- **`CLAUDE.md` and `TODO.md` content.** Reviewed; per user preference,
  intentionally retained. Both are accurate and useful contributor
  context.

---

## Audit metadata

- Repo state: HEAD at `00b67f5` ("Merge pull request #6 …"), 20 commits
  total across history.
- Tooling used in this environment: `detect-secrets` (installed for the
  scan), `git grep`, `git log`, custom Python PNG-chunk parser,
  `pytest`, `ruff`, `black`. `gitleaks` and `trufflehog` were not
  available; detect-secrets + targeted greps were used as the
  equivalent coverage.
- Verification commands run during the audit:
  - `QT_QPA_PLATFORM=offscreen python -m pytest -q src` → 163 passed
  - `ruff check src` → clean
  - `black --check src` → clean
  - `python src/eq_parser.py Gorrek --log-folder samples …` → success
