"""Renders the travel map: Pillow drawing over the EverQuest world map.

``MapRenderer`` overlays ``zone_map.png`` with travel lines and dots.
Per-zone pixel coordinates live in ``zone_graph.json`` and are looked up
via ``zone_graph.get_zone_center``.
"""

from pathlib import Path

from PIL import Image, ImageDraw

import resource_paths
from zone_graph import get_zone_center, has_zone_center  # noqa: F401


def _data_root():
    bundle = resource_paths.bundled_root()
    if bundle is not None:
        return bundle / "data"
    return Path(__file__).resolve().parents[1] / "data"


MAP_IMAGE_PATH = _data_root() / "zone_map.png"

LINE_WIDTH = 2
DOT_RADIUS = 2
LOCATION_CIRCLE_RADIUS = 30
LOCATION_CIRCLE_WIDTH = 10
MAP_PIXEL_WIDTH = 2700
MAP_PIXEL_HEIGHT = 1550
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
    def __init__(self, map_image_path=MAP_IMAGE_PATH, base_image=None):
        self.image = Image.new(
            "RGBA", (MAP_PIXEL_WIDTH, MAP_PIXEL_HEIGHT), (0, 0, 0, 0)
        )
        self.draw = ImageDraw.Draw(self.image, "RGBA")

        # ``base_image`` lets callers (e.g. the video generator) reuse an
        # already-loaded map and skip re-reading the PNG from disk on every
        # incremental re-render.
        if base_image is not None:
            map_image = base_image
        else:
            map_image = Image.open(map_image_path).convert("RGBA")
        if map_image.size != (MAP_PIXEL_WIDTH, MAP_PIXEL_HEIGHT):
            map_image = map_image.resize(
                (MAP_PIXEL_WIDTH, MAP_PIXEL_HEIGHT), Image.LANCZOS
            )
        self.image.paste(map_image, (0, 0))

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

    def draw_disc(self, center, radius, percent):
        x, y = center
        self.draw.ellipse(
            [(x - radius, y - radius), (x + radius, y + radius)],
            fill=_to_rgba(make_rainbow(percent)),
        )

    def draw_location_circle(self, zone_loc, percent):
        x, y = zone_loc
        r = LOCATION_CIRCLE_RADIUS
        w = LOCATION_CIRCLE_WIDTH
        o = 2
        color = _to_rgba(make_rainbow(percent))
        black = (0, 0, 0, 255)
        self.draw.ellipse(
            [(x - r - o, y - r - o), (x + r + o, y + r + o)],
            outline=black,
            width=o,
        )
        self.draw.ellipse(
            [(x - r, y - r), (x + r, y + r)],
            outline=color,
            width=w,
        )
        self.draw.ellipse(
            [(x - r + w, y - r + w), (x + r - w, y + r - w)],
            outline=black,
            width=o,
        )

    @classmethod
    def for_overlay(cls, image):
        """Return a renderer that draws onto *image* without pasting a base map."""
        obj = cls.__new__(cls)
        obj.image = image
        obj.draw = ImageDraw.Draw(image, "RGBA")
        return obj

    def get_image(self):
        return self.image.copy()

    def display_map(self):
        self.image.show()

    def save_map(self, output_path):
        self.image.save(output_path, format="PNG")


# Outer radius of the busiest zone's colour ring, in map pixels. Matches the
# old maximum jitter radius (``MAX_JITTER_SIZE / 2``) so the visual spread of a
# busy zone is unchanged, while the placement is now deterministic. Other zones
# scale down from here by visit count (see ``map_path``).
MAX_RING_RADIUS = 18.75

# Floor on a zone's outer radius so rarely-visited zones stay visible rather
# than shrinking to a sub-pixel dot.
MIN_RING_RADIUS = 7.5


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
