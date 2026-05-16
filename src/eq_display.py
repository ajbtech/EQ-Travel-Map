"""Renders the travel map: Pillow drawing over the EverQuest world map.

``MapRenderer`` overlays ``zone_map.png`` with travel lines, dots, and an
optional metrics panel. Per-zone pixel coordinates live in ``zone_graph.json``
and are looked up via ``zone_graph.get_zone_center``.
"""

import sys
from pathlib import Path
from random import random

from PIL import Image, ImageDraw, ImageFont

from zone_graph import get_zone_center, has_zone_center  # noqa: F401


def _data_root():
    if hasattr(sys, "_MEIPASS"):
        return Path(sys._MEIPASS)
    return Path(__file__).resolve().parents[1]


MAP_IMAGE_PATH = _data_root() / "zone_map.png"
FONT_DIR = _data_root() / "assets" / "fonts"
FONT_REGULAR_PATH = FONT_DIR / "DejaVuSansMono.ttf"
FONT_BOLD_PATH = FONT_DIR / "DejaVuSansMono-Bold.ttf"

LINE_WIDTH = 2
DOT_RADIUS = 2
MAP_PIXEL_WIDTH = 2700
MAP_PIXEL_HEIGHT = 1550
METRICS_PANEL_PIXEL_WIDTH = 700
METRICS_PANEL_BACKGROUND = (244, 239, 228, 255)  # #f4efe4
METRICS_TEXT_COLOR = (36, 28, 20, 255)  # #241c14
METRICS_HEADING_FONT_PX = 18
METRICS_BODY_FONT_PX = 14
METRICS_HEADING_LINE_PX = 53
METRICS_BODY_LINE_PX = 45
METRICS_BLANK_LINE_PX = 28
METRICS_LEFT_MARGIN_FRACTION = 0.07
METRICS_TOP_MARGIN_PX = 54
RAINBOW_COLOR_STOPS = [
    (0, (1, 0, 0)),
    (0.1, (1, 1, 0)),
    (0.3, (0, 1, 0)),
    (0.5, (0, 1, 1)),
    (0.7, (0, 0, 1)),
    (0.9, (1, 0, 1)),
    (1, (1, 0, 0)),
]


def _to_rgba(color_0_1, alpha=255):
    r, g, b = color_0_1
    return (int(round(r * 255)), int(round(g * 255)), int(round(b * 255)), alpha)


class MapRenderer:
    def __init__(self, map_image_path=MAP_IMAGE_PATH, include_metrics_panel=False):
        self.include_metrics_panel = include_metrics_panel
        total_width = self._get_total_width(include_metrics_panel)

        # Use a fully transparent base when there is no metrics panel so
        # ``save_map`` can write a PNG with a transparent border; the metrics
        # panel needs an opaque cream background to keep text legible.
        base_color = (0, 0, 0, 0) if not include_metrics_panel else METRICS_PANEL_BACKGROUND
        self.image = Image.new("RGBA", (total_width, MAP_PIXEL_HEIGHT), base_color)
        self.draw = ImageDraw.Draw(self.image, "RGBA")

        map_image = Image.open(map_image_path).convert("RGBA")
        if map_image.size != (MAP_PIXEL_WIDTH, MAP_PIXEL_HEIGHT):
            map_image = map_image.resize(
                (MAP_PIXEL_WIDTH, MAP_PIXEL_HEIGHT), Image.LANCZOS
            )
        self.image.paste(map_image, (0, 0))

        self._heading_font = None
        self._body_font = None

    def _get_total_width(self, include_metrics_panel):
        if include_metrics_panel:
            return MAP_PIXEL_WIDTH + METRICS_PANEL_PIXEL_WIDTH
        return MAP_PIXEL_WIDTH

    def _load_fonts(self):
        if self._heading_font is None:
            self._heading_font = ImageFont.truetype(
                str(FONT_BOLD_PATH), METRICS_HEADING_FONT_PX
            )
            self._body_font = ImageFont.truetype(
                str(FONT_REGULAR_PATH), METRICS_BODY_FONT_PX
            )

    def draw_line(self, zone_loc_1, zone_loc_2, percent):
        self.draw.line(
            [zone_loc_1, zone_loc_2],
            fill=_to_rgba(make_rainbow(percent)),
            width=LINE_WIDTH,
        )

    def draw_dot(self, zone_loc, percent):
        x, y = zone_loc
        self.draw.ellipse(
            [(x - DOT_RADIUS, y - DOT_RADIUS), (x + DOT_RADIUS, y + DOT_RADIUS)],
            fill=_to_rgba(make_rainbow(percent)),
        )

    def draw_metrics(self, lines):
        if not self.include_metrics_panel:
            raise ValueError(
                "MapRenderer must be created with include_metrics_panel=True "
                "before metrics can be drawn."
            )

        self._load_fonts()
        x = MAP_PIXEL_WIDTH + int(
            METRICS_LEFT_MARGIN_FRACTION * METRICS_PANEL_PIXEL_WIDTH
        )
        y = METRICS_TOP_MARGIN_PX

        for line in lines:
            if line == "":
                y += METRICS_BLANK_LINE_PX
                continue

            is_heading = line.endswith(":")
            font = self._heading_font if is_heading else self._body_font
            self.draw.text((x, y), line, fill=METRICS_TEXT_COLOR, font=font)
            y += METRICS_HEADING_LINE_PX if is_heading else METRICS_BODY_LINE_PX

    def display_map(self):
        self.image.show()

    def save_map(self, output_path):
        self.image.save(output_path, format="PNG")


MAX_JITTER_SIZE = 37.5
MIN_VISITS_TO_MAX_JITTER = 25


def get_jitter_scale(visit_number, total_visits=MIN_VISITS_TO_MAX_JITTER):
    if visit_number <= 1:
        return 0
    visits_to_max_jitter = max(total_visits, MIN_VISITS_TO_MAX_JITTER)
    return min((visit_number - 1) / (visits_to_max_jitter - 1), 1)


def get_shifted_zone_center(
    key,
    visit_number=MIN_VISITS_TO_MAX_JITTER,
    total_visits=MIN_VISITS_TO_MAX_JITTER,
):
    r_size = MAX_JITTER_SIZE * get_jitter_scale(visit_number, total_visits)
    x, y = get_zone_center(key)
    return (x + (random() - 0.5) * r_size, y + (random() - 0.5) * r_size)


def make_rainbow(percent):
    for start_stop, end_stop in zip(RAINBOW_COLOR_STOPS, RAINBOW_COLOR_STOPS[1:]):
        start_percent, start_color = start_stop
        end_percent, end_color = end_stop
        if percent <= end_percent:
            return interpolate_color(
                start_color,
                end_color,
                (percent - start_percent) / (end_percent - start_percent),
            )
    return RAINBOW_COLOR_STOPS[-1][1]


def interpolate_color(start_color, end_color, percent):
    return tuple(
        start_color[index] + (end_color[index] - start_color[index]) * percent
        for index in range(3)
    )
