"""Command-line entry point for the EverQuest Travel Map.

Wires the log parser, summary formatter, and map renderer together so that
running ``python src/eq_parser.py <Character>`` produces a saved map image
and prints a text summary to stdout.
"""

import argparse
from pathlib import Path

import eq_display
import log_parser
import map_path
import summary_formatter

_PROJECT_ROOT = Path(__file__).resolve().parents[1]

_CANDIDATE_LOG_FOLDERS = (
    Path.home() / "EverQuest" / "Logs",
    Path("C:/EverQuest/Logs"),
    Path("C:/Program Files/Sony/EverQuest/Logs"),
    Path("C:/Program Files (x86)/Sony/EverQuest/Logs"),
)


def _detect_default_log_folder():
    for candidate in _CANDIDATE_LOG_FOLDERS:
        if candidate.is_dir():
            return candidate
    bundled_samples = _PROJECT_ROOT / "samples"
    if bundled_samples.is_dir():
        return bundled_samples
    return Path.home()


DEFAULT_LOG_FOLDER_PATH = _detect_default_log_folder()
DEFAULT_MAP_OUTPUT_PATH = Path.home() / "everquest_travel_map.png"


def draw_zone_path(my_zone_list, output_path=None):
    zone_list = my_zone_list.get_raw_eq_list()

    if len(zone_list) == 0:
        print("No zones found; skipping map display.")
        return

    if not map_path.get_known_zones(zone_list):
        print("No known zones found; skipping map display.")
        return
    draw_events = map_path.build_map_events(zone_list)

    map_renderer = eq_display.MapRenderer()

    # Draw newest events first so older low-level routes remain visible on top.
    for draw_event in reversed(draw_events):
        draw_map_event(map_renderer, draw_event)

    if output_path is None:
        map_renderer.display_map()
    else:
        map_renderer.save_map(output_path)


def draw_map_event(map_renderer, draw_event):
    draw_event.draw(map_renderer)


def build_arg_parser():
    parser = argparse.ArgumentParser(
        description=("Parse EverQuest logs for a character and generate a travel map."),
    )
    parser.add_argument(
        "character_name",
        help="Character name as it appears in eqlog_<Character>_*.txt files.",
    )
    parser.add_argument(
        "--log-folder",
        default=DEFAULT_LOG_FOLDER_PATH,
        type=Path,
        help="Folder containing EverQuest log files.",
    )
    parser.add_argument(
        "--output",
        default=DEFAULT_MAP_OUTPUT_PATH,
        type=Path,
        help="Path where the generated map image should be saved.",
    )
    return parser


def main(character_name, log_folder_path=DEFAULT_LOG_FOLDER_PATH, output_path=None):
    if output_path is None:
        output_path = DEFAULT_MAP_OUTPUT_PATH

    my_kill_list, my_zone_list, summary = log_parser.parse_character_logs(
        log_folder_path,
        character_name,
    )
    summary_lines = summary_formatter.build_summary_lines(
        my_kill_list,
        my_zone_list,
        summary,
        character_name,
    )

    print(*summary_lines, sep="\n")
    draw_zone_path(my_zone_list, output_path=output_path)


if __name__ == "__main__":
    args = build_arg_parser().parse_args()
    main(args.character_name, args.log_folder, args.output)
