from collections import Counter
from dataclasses import dataclass

import eq_display
import zone_graph


@dataclass(frozen=True)
class MapLine:
    start_loc: tuple[float, float]
    end_loc: tuple[float, float]
    percent: float

    def draw(self, renderer):
        renderer.draw_line(self.start_loc, self.end_loc, percent=self.percent)


@dataclass(frozen=True)
class MapDot:
    loc: tuple[float, float]
    percent: float

    def draw(self, renderer):
        renderer.draw_dot(self.loc, percent=self.percent)


def _emits_event(last_zone, zone):
    """Whether moving from *last_zone* to *zone* produces a draw event.

    Single source of truth shared with ``cumulative_event_counts`` so the two
    can't drift: a prefix of the events always maps to a prefix of the
    known-zone sequence. A move emits when the zones are graph-adjacent (a line)
    or are genuinely different but non-adjacent (a jump dot); revisiting the
    same zone emits nothing.
    """
    if last_zone == "":
        return False
    return zone_graph.are_adjacent(last_zone, zone) or not zone_graph.is_same_zone(
        last_zone, zone
    )


def build_map_events(zone_list):
    known_zone_list = get_known_zones(zone_list)
    if len(known_zone_list) == 0:
        return []

    last_zone = ""
    last_loc = None
    zone_count = len(known_zone_list)
    percent_inc = 1 / zone_count
    percent = 0
    draw_events = []
    zone_visit_counts = {}
    zone_total_counts = Counter(known_zone_list)

    for zone in known_zone_list:
        zone_visit_counts[zone] = zone_visit_counts.get(zone, 0) + 1
        loc = eq_display.get_shifted_zone_center(
            zone,
            zone_visit_counts[zone],
            zone_total_counts[zone],
        )
        if _emits_event(last_zone, zone):
            if zone_graph.are_adjacent(last_zone, zone):
                draw_events.append(MapLine(last_loc, loc, percent))
            else:
                # Ports, deaths, and logging gaps can jump across the graph;
                # mark the destination without drawing an impossible line.
                draw_events.append(MapDot(loc, percent))
            percent += percent_inc
        last_zone = zone
        last_loc = loc

    return draw_events


def get_known_zones(zone_list):
    return [zone for zone in zone_list if zone_graph.has_zone_center(zone)]


def cumulative_event_counts(zone_list):
    """Running count of draw events after each known zone is processed.

    Mirrors ``build_map_events``'s emit condition (which is deterministic and
    independent of jitter) so a prefix of the events maps to a prefix of the
    known-zone sequence. ``counts[-1] == len(build_map_events(zone_list))``.
    """
    counts = []
    event_count = 0
    last_zone = ""
    for zone in get_known_zones(zone_list):
        if _emits_event(last_zone, zone):
            event_count += 1
        last_zone = zone
        counts.append(event_count)
    return counts
