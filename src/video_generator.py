"""Builds per-frame data for the travel-replay video.

Walks a ``ParseSummary.timeline`` in chronological order, batching events into
frames so the whole journey fits the requested duration. Each frame carries the
current map image (travel lines revealed so far, drawn newest-underneath like
the static map) plus the running summary columns. Pure Python / Pillow: no Qt
here so it stays unit-testable.
"""

from collections import Counter
from dataclasses import dataclass

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
        event_count = len(self._timeline)
        total = self._total_frames

        login_count = 0
        death_count = 0
        kill_count = 0
        zone_count = 0
        level_lost_count = 0
        current_level = 1
        loot_cash = money_sorter.Cash()
        merch_cash = money_sorter.Cash()
        kill_counter = Counter()
        zone_counter = Counter()

        known_revealed = 0
        drawn_event_count = 0
        current_map_image = self._base_image
        last_known_zone = None

        consumed = 0
        for frame_index in range(total):
            target_consumed = self._events_through_frame(
                frame_index, event_count, total
            )
            while consumed < target_consumed:
                event = self._timeline[consumed]
                consumed += 1
                kind = event.kind
                if kind == line_reader.EventType.ZONE:
                    zone_count += 1
                    zone_counter[event.value] += 1
                    if zone_graph.has_zone_center(event.value):
                        known_revealed += 1
                        last_known_zone = event.value
                elif kind == line_reader.EventType.KILL:
                    kill_count += 1
                    kill_counter[event.value] += 1
                elif kind == line_reader.EventType.DEATH:
                    death_count += 1
                elif kind == line_reader.EventType.LOGIN:
                    login_count += 1
                elif kind == line_reader.EventType.LEVEL_GAINED:
                    current_level = event.value
                elif kind == line_reader.EventType.LEVEL_LOST:
                    level_lost_count += 1
                    current_level = event.value
                elif kind == line_reader.EventType.LOOT_CASH:
                    loot_cash = loot_cash.add(event.value)
                elif kind == line_reader.EventType.MERCHANT_CASH:
                    merch_cash = merch_cash.add(event.value)

            target_events = (
                self._cumulative[known_revealed - 1] if known_revealed else 0
            )
            if target_events > drawn_event_count:
                current_map_image = self._render_map(target_events, last_known_zone)
                drawn_event_count = target_events

            yield VideoFrame(
                map_image=current_map_image,
                top_kills_lines=self._top_lines("Top 5 killed creatures", kill_counter),
                top_zones_lines=self._top_lines("Top 5 visited zones", zone_counter),
                stats_lines=self._stats_lines(
                    login_count,
                    death_count,
                    zone_count,
                    kill_count,
                    level_lost_count,
                    loot_cash,
                    merch_cash,
                ),
                level_line=f"Level: {summary_formatter.format_number(current_level)}",
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
        renderer = eq_display.MapRenderer(base_image=self._base_image)
        events = self._all_map_events[:event_count]
        for event in reversed(events):
            event.draw(renderer)
        if last_known_zone is not None and events:
            loc = eq_display.get_zone_center(last_known_zone)
            renderer.draw_location_circle(loc, events[-1].percent)
        return renderer.get_image()

    @staticmethod
    def _top_lines(title, counter):
        lines = [f"{title}:"]
        ranked = sorted(counter.items(), key=lambda item: (-item[1], item[0].lower()))
        for rank, (name, count) in enumerate(ranked[:TOP_LIMIT], 1):
            lines.append(f"{rank}. {name}: {summary_formatter.format_number(count)}")
        return lines

    def _stats_lines(
        self,
        login_count,
        death_count,
        zone_count,
        kill_count,
        level_lost_count,
        loot_cash,
        merch_cash,
    ):
        fmt = summary_formatter.format_number
        return [
            f"First log: {self._first_login_message.rstrip()}",
            f"Total logs: {fmt(self._line_count)}",
            f"Logins: {fmt(login_count)}",
            f"Deaths: {fmt(death_count)}",
            f"Zone Count: {fmt(zone_count)}",
            f"Kill Count: {fmt(kill_count)}",
            f"Levels Lost: {fmt(level_lost_count)}",
            f"Looted coin: {summary_formatter.format_cash(loot_cash.normalize())}",
            f"Coin from Merchants: "
            f"{summary_formatter.format_cash(merch_cash.normalize())}",
        ]
