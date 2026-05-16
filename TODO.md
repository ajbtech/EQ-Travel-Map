# TODO

## Bugs
- [ ] Remove coin from looting own corpse
- [ ] Fix zone centers which are off, particularly in Kunark
- [ ] Fix capitalization of loot

## Features
- [ ] Add a view that allows a live run of the travel map
- [ ] Allow zoom and pan in the map
- [x] Allow dynamic app resizing

## Polish
- [ ] Fix bevel so it matches the original UI style
- [ ] Fix button style to match the original EverQuest UI
- [ ] Fix overall sizing in the input window
- [ ] Add title and character name
- [ ] Incorporate original style of hp/mana bar somewhere
- [ ] Revise updated UI
- [x] Remove 90% of combat text from the example file to reduce size
- [x] Remove all say, shout, ooc and guild chat from the example text

## Pre-tag (before v0.1.0 release)
- [ ] Capture proper GUI screenshots (input view + results view) on a real desktop session and add to `docs/`. The Qt offscreen platform can't load system fonts so screenshots have to come from a normal interactive run.

## Good first issues (post v0.1.0, file as GitHub issues after first push)
- [x] Move `ZONE_CENTERS` from `src/eq_display.py` into a JSON data file alongside `zone_graph.json`
- [ ] Rename verbose accessor methods in `src/eq_list.py` (e.g. `get_count_alpha_sorted_eq_list` -> shorter form)
- [ ] Add tests for the UI views (`InputView`, `ProgressView`, `ResultsView`) and widgets (`MapCanvas`, `ParchmentPanel`, `EngravedHeading`)
- [ ] Replace `src/desktop_app.py`'s `sys.path` shim with a proper `python -m` entry point
- [ ] Drop the redundant `get_plat`/`get_gold`/`get_silver`/`get_copper` wrappers in `src/money_sorter.py` in favor of `get_coin_value()`
- [ ] Replace the placeholder pixel-art icon with commissioned art

## Deferred / Maybe

## Done
