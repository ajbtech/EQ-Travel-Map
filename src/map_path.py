import math
from collections import Counter
from dataclasses import dataclass

import eq_display
import zone_graph


@dataclass(frozen=True)
class ZoneVisit:
    """One visit to a known zone, drawn as a colour ring (plus an optional line).

    Each visit paints a filled disc centred on the zone. A zone's visits stack
    into concentric discs: the first visit is the small inner disc and the last
    visit is the full-radius outer disc, so the ring colour runs from the
    earliest visit's rainbow colour at the centre to the latest at the edge.
    The zone's outer radius scales with how often it was visited — its disc
    *area* is proportional to its visit count relative to the busiest zone, so
    the most-visited zone fills ``MAX_RING_RADIUS`` and the rest shrink from
    there. ``line_start``/``line_end`` carry the connecting line from the
    previous visit when (and only when) the two zones are graph-adjacent; the
    line attaches to each circle at the matching visit's ring radius.
    """

    center: tuple[float, float]
    radius: float
    percent: float
    line_start: tuple[float, float] | None = None
    line_end: tuple[float, float] | None = None

    def draw(self, renderer):
        if self.line_start is not None:
            renderer.draw_line(self.line_start, self.line_end, percent=self.percent)
        renderer.draw_disc(self.center, self.radius, percent=self.percent)


def build_map_events(zone_list):
    known_zone_list = get_known_zones(zone_list)
    visit_count = len(known_zone_list)
    if visit_count == 0:
        return []

    zone_total_counts = Counter(known_zone_list)
    max_total = max(zone_total_counts.values())
    zone_visit_counts = {}
    draw_events = []
    last_zone = ""
    last_center = None
    last_radius = 0.0

    for visit_index, zone in enumerate(known_zone_list):
        percent = _visit_percent(visit_index, visit_count)
        zone_visit_counts[zone] = zone_visit_counts.get(zone, 0) + 1
        radius = _visit_radius(
            zone_visit_counts[zone], zone_total_counts[zone], max_total
        )
        center = eq_display.get_zone_center(zone)

        line_start, line_end = _connecting_line(
            last_zone, zone, last_center, last_radius, center, radius
        )
        draw_events.append(ZoneVisit(center, radius, percent, line_start, line_end))

        last_zone = zone
        last_center = center
        last_radius = radius

    return draw_events


def _visit_percent(visit_index, visit_count):
    """Chronological rainbow position of a visit, from red (first) to violet (last)."""
    if visit_count == 1:
        return 0.0
    return visit_index / (visit_count - 1)


def _zone_outer_radius(total_visits, max_total):
    """Full radius of a zone, with disc *area* proportional to its visit share.

    The busiest zone (``total_visits == max_total``) fills ``MAX_RING_RADIUS``;
    a zone visited a quarter as often covers a quarter of the area, i.e. half
    the radius.
    """
    return eq_display.MAX_RING_RADIUS * math.sqrt(total_visits / max_total)


def _visit_radius(visit_number, total_visits, max_total):
    """Radius of a single ring within a zone's area-scaled outer circle."""
    outer_radius = _zone_outer_radius(total_visits, max_total)
    return outer_radius * visit_number / total_visits


def _connecting_line(last_zone, zone, last_center, last_radius, center, radius):
    """Endpoints of the line into *zone*, or ``(None, None)`` when none is drawn.

    A line is drawn only for genuine graph-adjacent moves. It runs from the
    previous zone's ring (at that visit's radius) to this zone's ring, along the
    straight line between the two zone centres, so it meets each circle at the
    matching colour band.
    """
    no_line = (None, None)
    is_first_visit = last_zone == ""
    if is_first_visit or not zone_graph.are_adjacent(last_zone, zone):
        return no_line

    delta_x = center[0] - last_center[0]
    delta_y = center[1] - last_center[1]
    distance = math.hypot(delta_x, delta_y)
    centers_coincide = distance == 0
    circles_overlap = last_radius + radius >= distance
    if centers_coincide or circles_overlap:
        return no_line

    unit_x = delta_x / distance
    unit_y = delta_y / distance
    start = (
        last_center[0] + unit_x * last_radius,
        last_center[1] + unit_y * last_radius,
    )
    end = (center[0] - unit_x * radius, center[1] - unit_y * radius)
    return (start, end)


def get_known_zones(zone_list):
    return [zone for zone in zone_list if zone_graph.has_zone_center(zone)]


def cumulative_event_counts(zone_list):
    """Running count of draw events after each known zone is processed.

    Every known visit emits exactly one :class:`ZoneVisit`, so the count after
    the k-th known zone is simply k. Keeping this in lockstep with
    ``build_map_events`` means a prefix of the events always maps to a prefix of
    the known-zone sequence: ``counts[-1] == len(build_map_events(zone_list))``.
    """
    return list(range(1, len(get_known_zones(zone_list)) + 1))
