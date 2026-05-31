"""Builds per-frame data for the travel-replay video.

Walks a ``ParseSummary.timeline`` in chronological order, batching events into
frames so the whole journey fits the requested duration. Each frame carries the
current map image (travel lines revealed so far, drawn newest-underneath like
the static map) plus the running summary columns. Pure Python / Pillow: no Qt
here so it stays unit-testable.
"""

from collections import Counter
from dataclasses import dataclass

from PIL import Image

import eq_display
import line_reader
import map_path
import money_sorter
import summary_formatter
import zone_graph

FPS = 24
DEFAULT_TARGET_SECONDS = 120
TOP_LIMIT = 5


@dataclass
class VideoFrame:
    map_image: object
    top_kills_lines: list
    top_zones_lines: list
    stats_lines: list
    level_line: str
    frame_index: int
    total_frames: int
    map_updated: bool
    content_version: int


def _apply_zone(totals, event):
    totals.zone_count += 1
    totals.zone_counter[event.value] += 1
    if zone_graph.has_zone_center(event.value):
        totals.known_revealed += 1
        totals.last_known_zone = event.value


def _apply_kill(totals, event):
    totals.kill_count += 1
    totals.kill_counter[event.value] += 1


def _apply_death(totals, _event):
    totals.death_count += 1


def _apply_login(totals, _event):
    totals.login_count += 1


def _apply_level_gained(totals, event):
    totals.current_level = event.value


def _apply_level_lost(totals, event):
    totals.level_lost_count += 1
    totals.current_level = event.value


def _apply_loot_cash(totals, event):
    totals.loot_cash = totals.loot_cash.add(event.value)


def _apply_merchant_cash(totals, event):
    totals.merch_cash = totals.merch_cash.add(event.value)


# Table-driven dispatch (mirrors log_parser.EVENT_HANDLERS) so adding a tracked
# event is one entry rather than another branch in the frame loop.
_TOTALS_HANDLERS = {
    line_reader.EventType.ZONE: _apply_zone,
    line_reader.EventType.KILL: _apply_kill,
    line_reader.EventType.DEATH: _apply_death,
    line_reader.EventType.LOGIN: _apply_login,
    line_reader.EventType.LEVEL_GAINED: _apply_level_gained,
    line_reader.EventType.LEVEL_LOST: _apply_level_lost,
    line_reader.EventType.LOOT_CASH: _apply_loot_cash,
    line_reader.EventType.MERCHANT_CASH: _apply_merchant_cash,
}


class _RunningTotals:
    """Replayable tally of the metrics shown as the video progresses.

    ``apply`` consumes one timeline event; ``known_revealed`` /
    ``last_known_zone`` track which map segments should be drawn so the frame
    loop can stay focused on pacing and rendering.
    """

    def __init__(self):
        self.login_count = 0
        self.death_count = 0
        self.kill_count = 0
        self.zone_count = 0
        self.level_lost_count = 0
        self.current_level = 1
        self.loot_cash = money_sorter.Cash()
        self.merch_cash = money_sorter.Cash()
        self.kill_counter = Counter()
        self.zone_counter = Counter()
        self.known_revealed = 0
        self.last_known_zone = None

    def apply(self, event):
        handler = _TOTALS_HANDLERS.get(event.kind)
        if handler is not None:
            handler(self, event)


class VideoGenerator:
    def __init__(
        self,
        character_name,
        zone_list,
        parse_summary,
        target_seconds=DEFAULT_TARGET_SECONDS,
        fps=FPS,
    ):
        self.character_name = character_name
        self.fps = fps
        self.target_seconds = target_seconds

        self._timeline = list(parse_summary.timeline)
        self._first_login_message = parse_summary.first_login_message
        self._line_count = parse_summary.line_count

        raw_zones = zone_list.get_raw_eq_list()
        self._all_map_events = map_path.build_map_events(raw_zones)
        self._cumulative = map_path.cumulative_event_counts(raw_zones)
        self._base_image = eq_display.MapRenderer().get_image()

        event_count = len(self._timeline)
        if event_count == 0:
            self._total_frames = 1
        else:
            target_frames = max(1, int(round(self.target_seconds * self.fps)))
            self._total_frames = min(event_count, target_frames)

    def total_frames(self):
        return self._total_frames

    def frames(self):
        # Reset incremental render state so frames() is safe to call multiple times.
        self._lines_overlay = Image.new(
            "RGBA",
            (eq_display.MAP_PIXEL_WIDTH, eq_display.MAP_PIXEL_HEIGHT),
            (0, 0, 0, 0),
        )
        self._rendered_event_count = 0

        event_count = len(self._timeline)
        total = self._total_frames

        totals = _RunningTotals()
        drawn_event_count = 0
        current_map_image = self._base_image
        prev_consumed = 0
        content_version = 0

        consumed = 0
        for frame_index in range(total):
            target_consumed = self._events_through_frame(
                frame_index, event_count, total
            )
            while consumed < target_consumed:
                totals.apply(self._timeline[consumed])
                consumed += 1

            target_events = (
                self._cumulative[totals.known_revealed - 1]
                if totals.known_revealed
                else 0
            )
            map_was_updated = False
            if target_events > drawn_event_count:
                current_map_image = self._render_map(
                    target_events, totals.last_known_zone
                )
                drawn_event_count = target_events
                map_was_updated = True

            if consumed != prev_consumed:
                content_version += 1
                prev_consumed = consumed

            yield VideoFrame(
                map_image=current_map_image,
                map_updated=map_was_updated,
                content_version=content_version,
                top_kills_lines=self._top_lines(
                    "Top 5 killed creatures", totals.kill_counter
                ),
                top_zones_lines=self._top_lines(
                    "Top 5 visited zones", totals.zone_counter
                ),
                stats_lines=self._stats_lines(totals),
                level_line=(
                    f"Level: {summary_formatter.format_number(totals.current_level)}"
                ),
                frame_index=frame_index,
                total_frames=total,
            )

    @staticmethod
    def _events_through_frame(frame_index, event_count, total):
        if total == 0:
            return event_count
        if frame_index == total - 1:
            return event_count
        return int(round((frame_index + 1) * event_count / total))

    def _render_map(self, event_count, last_known_zone=None):
        new_events = self._all_map_events[self._rendered_event_count : event_count]
        if new_events:
            # Draw new events onto a fresh transparent layer.  Reversing within
            # the batch keeps the same "oldest on top" z-order as a full redraw:
            # the earliest of the new events is drawn last and sits on top of the
            # later ones.
            new_layer = Image.new(
                "RGBA",
                (eq_display.MAP_PIXEL_WIDTH, eq_display.MAP_PIXEL_HEIGHT),
                (0, 0, 0, 0),
            )
            overlay_renderer = eq_display.MapRenderer.for_overlay(new_layer)
            for event in reversed(new_events):
                event.draw(overlay_renderer)
            # Paste the existing lines on top so all previously drawn events
            # remain above the new ones, preserving the overall z-order.
            new_layer.alpha_composite(self._lines_overlay)
            self._lines_overlay = new_layer
            self._rendered_event_count = event_count

        result = self._base_image.copy()
        result.alpha_composite(self._lines_overlay)
        if last_known_zone is not None and event_count > 0:
            loc = eq_display.get_zone_center(last_known_zone)
            circle_renderer = eq_display.MapRenderer.for_overlay(result)
            circle_renderer.draw_location_circle(
                loc, self._all_map_events[event_count - 1].percent
            )
        return result

    @staticmethod
    def _top_lines(title, counter):
        lines = [f"{title}:"]
        ranked = sorted(counter.items(), key=lambda item: (-item[1], item[0].lower()))
        for rank, (name, count) in enumerate(ranked[:TOP_LIMIT], 1):
            lines.append(f"{rank}. {name}: {summary_formatter.format_number(count)}")
        return lines

    def _stats_lines(self, totals):
        fmt = summary_formatter.format_number
        cash = summary_formatter.format_cash
        return [
            f"First log: {self._first_login_message.rstrip()}",
            f"Total logs: {fmt(self._line_count)}",
            f"Logins: {fmt(totals.login_count)}",
            f"Deaths: {fmt(totals.death_count)}",
            f"Zone Count: {fmt(totals.zone_count)}",
            f"Kill Count: {fmt(totals.kill_count)}",
            f"Levels Lost: {fmt(totals.level_lost_count)}",
            f"Looted coin: {cash(totals.loot_cash.normalize())}",
            f"Coin from Merchants: {cash(totals.merch_cash.normalize())}",
        ]
