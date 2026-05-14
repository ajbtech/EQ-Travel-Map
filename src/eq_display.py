"""Renders the travel map: matplotlib drawing over the EverQuest world map.

``MapRenderer`` overlays ``zone_map.png`` with travel lines, dots, and an
optional metrics panel. Per-zone pixel coordinates live in ``zone_graph.json``
and are looked up via ``zone_graph.get_zone_center``.
"""

import sys
from pathlib import Path
from random import random

import matplotlib

# Must be selected before importing pyplot so map rendering does not depend on Tk.
matplotlib.use("Agg")

import matplotlib.image as img  # noqa: E402
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.patches import Rectangle  # noqa: E402

from zone_graph import get_zone_center, has_zone_center  # noqa: E402,F401


def _data_root():
    if hasattr(sys, "_MEIPASS"):
        return Path(sys._MEIPASS)
    return Path(__file__).resolve().parents[1]


MAP_IMAGE_PATH = _data_root() / "zone_map.png"
LINE_WIDTH = 1.5
MAP_PIXEL_WIDTH = 2700
MAP_PIXEL_HEIGHT = 1550
METRICS_PANEL_PIXEL_WIDTH = 700
DPI = 100
METRICS_PANEL_BACKGROUND = "#f4efe4"
METRICS_TEXT_COLOR = "#241c14"
RAINBOW_COLOR_STOPS = [
    (0, (1, 0, 0)),
    (0.1, (1, 1, 0)),
    (0.3, (0, 1, 0)),
    (0.5, (0, 1, 1)),
    (0.7, (0, 0, 1)),
    (0.9, (1, 0, 1)),
    (1, (1, 0, 0)),
]


class MapRenderer:
    def __init__(self, map_image_path=MAP_IMAGE_PATH, include_metrics_panel=False):
        self.include_metrics_panel = include_metrics_panel
        total_width = self._get_total_width(include_metrics_panel)
        map_width = MAP_PIXEL_WIDTH / total_width

        self.fig = self._create_figure(total_width)
        self.ax = self._add_map_axis(map_width, map_image_path)
        self.metrics_ax = None
        if include_metrics_panel:
            self.metrics_ax = self._add_metrics_axis(map_width)

    def _get_total_width(self, include_metrics_panel):
        if include_metrics_panel:
            return MAP_PIXEL_WIDTH + METRICS_PANEL_PIXEL_WIDTH
        return MAP_PIXEL_WIDTH

    def _create_figure(self, total_width):
        return plt.figure(
            frameon=False,
            figsize=(total_width / DPI, MAP_PIXEL_HEIGHT / DPI),
            dpi=DPI,
            facecolor=METRICS_PANEL_BACKGROUND,
        )

    def _add_map_axis(self, map_width, map_image_path):
        map_axis = self.fig.add_axes([0, 0, map_width, 1])
        map_axis.axis("off")
        map_image = img.imread(map_image_path)
        map_axis.imshow(map_image)
        return map_axis

    def _add_metrics_axis(self, map_width):
        metrics_axis = self.fig.add_axes([map_width, 0, 1 - map_width, 1])
        self._style_metrics_axis(metrics_axis)
        return metrics_axis

    def _style_metrics_axis(self, metrics_ax):
        metrics_ax.set_facecolor(METRICS_PANEL_BACKGROUND)
        metrics_ax.set_xlim(0, 1)
        metrics_ax.set_ylim(0, 1)
        metrics_ax.axis("off")
        # Keep the panel opaque so text remains visible in dark-mode viewers.
        metrics_ax.add_patch(
            Rectangle(
                (0, 0),
                1,
                1,
                facecolor=METRICS_PANEL_BACKGROUND,
                edgecolor="none",
                zorder=0,
            )
        )

    def draw_line(self, zone_loc_1, zone_loc_2, percent):
        self.ax.plot(
            (zone_loc_1[0], zone_loc_2[0]),
            (zone_loc_1[1], zone_loc_2[1]),
            color=make_rainbow(percent),
            linewidth=LINE_WIDTH,
        )

    def draw_dot(self, zone_loc, percent):
        self.ax.plot(
            zone_loc[0],
            zone_loc[1],
            color=make_rainbow(percent),
            marker="o",
            markeredgewidth=0,
            markersize=LINE_WIDTH * 2,
        )

    def draw_metrics(self, lines):
        if self.metrics_ax is None:
            raise ValueError(
                "MapRenderer must be created with include_metrics_panel=True "
                "before metrics can be drawn."
            )

        y = 0.965
        for line in lines:
            if line == "":
                y -= 0.018
                continue

            is_heading = line.endswith(":")
            self.metrics_ax.text(
                0.07,
                y,
                line,
                color=METRICS_TEXT_COLOR,
                fontsize=13 if is_heading else 10,
                fontfamily="DejaVu Sans Mono",
                fontweight="bold" if is_heading else "normal",
                va="top",
                wrap=True,
                zorder=1,
            )
            y -= 0.034 if is_heading else 0.029

    def display_map(self):
        plt.show()

    def save_map(self, output_path):
        self.fig.savefig(
            output_path,
            pad_inches=0,
            transparent=not self.include_metrics_panel,
        )
        plt.close(self.fig)


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
