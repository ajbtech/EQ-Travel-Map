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
    previous visit when (and only when) the two zones are graph-adjacent. The
    line attaches to each circle at that visit's ring radius and is offset
    perpendicular to the route, so repeated trips between the same two zones fan
    out into a ribbon rather than stacking on one line.
    """

    center: tuple[float, float]
    radius: float
    percent: float
    line_start: tuple[float, float] | None = None
    line_end: tuple[float, float] | None = None

    def draw_disc(self, renderer):
        renderer.draw_disc(self.center, self.radius, percent=self.percent)

    def draw_line(self, renderer):
        if self.line_start is not None:
            renderer.draw_line(self.line_start, self.line_end, percent=self.percent)

    def draw(self, renderer):
        # Disc first, then the line on top, so the connecting ribbon is never
        # hidden behind the zone's filled circle.
        self.draw_disc(renderer)
        self.draw_line(renderer)


def build_map_events(zone_list):
    known_zone_list = get_known_zones(zone_list)
    visit_count = len(known_zone_list)
    if visit_count == 0:
        return []

    zone_total_counts = Counter(known_zone_list)
    max_total = max(zone_total_counts.values())
    corridor_keys = _corridor_keys(known_zone_list)
    corridor_totals = Counter(key for key in corridor_keys if key is not None)

    zone_visit_counts = {}
    corridor_seen = Counter()
    draw_events = []
    last_center = None
    last_radius = 0.0

    for visit_index, zone in enumerate(known_zone_list):
        percent = _visit_percent(visit_index, visit_count)
        zone_visit_counts[zone] = zone_visit_counts.get(zone, 0) + 1
        zone_total = zone_total_counts[zone]
        radius = _visit_radius(zone_visit_counts[zone], zone_total, max_total)
        center = eq_display.get_zone_center(zone)

        corridor_key = corridor_keys[visit_index]
        if corridor_key is None:
            line_start, line_end = (None, None)
        else:
            corridor_seen[corridor_key] += 1
            trip_index = corridor_seen[corridor_key] - 1
            line_start, line_end = _fanned_line(
                last_center,
                last_radius,
                center,
                radius,
                trip_index,
                corridor_totals[corridor_key],
            )
        draw_events.append(ZoneVisit(center, radius, percent, line_start, line_end))

        last_center = center
        last_radius = radius

    return draw_events


def _corridor_keys(known_zone_list):
    """Per-visit corridor key (the unordered zone pair) for each drawn move.

    Entry *i* is the route this visit's connecting line belongs to, or ``None``
    when the move emits no line (the first visit, a same-zone revisit, or a
    non-adjacent jump). Used to count and index the trips on each route so
    repeated trips can fan out into a ribbon.
    """
    keys = []
    last_zone = ""
    for zone in known_zone_list:
        if last_zone != "" and zone_graph.are_adjacent(last_zone, zone):
            keys.append(frozenset((last_zone, zone)))
        else:
            keys.append(None)
        last_zone = zone
    return keys


def _visit_percent(visit_index, visit_count):
    """Chronological rainbow position of a visit, from red (first) to violet (last)."""
    if visit_count == 1:
        return 0.0
    return visit_index / (visit_count - 1)


def _zone_outer_radius(total_visits, max_total):
    """Full radius of a zone, with disc *area* proportional to its visit share.

    The busiest zone (``total_visits == max_total``) fills ``MAX_RING_RADIUS``;
    a zone visited a quarter as often covers a quarter of the area, i.e. half
    the radius. The result is floored at ``MIN_RING_RADIUS`` so rarely-visited
    zones stay visible.
    """
    area_scaled_radius = eq_display.MAX_RING_RADIUS * math.sqrt(
        total_visits / max_total
    )
    return max(area_scaled_radius, eq_display.MIN_RING_RADIUS)


def _visit_radius(visit_number, total_visits, max_total):
    """Radius of a single ring within a zone's area-scaled outer circle."""
    outer_radius = _zone_outer_radius(total_visits, max_total)
    return outer_radius * visit_number / total_visits


def _fanned_line(last_center, last_radius, center, radius, trip_index, trip_total):
    """Endpoints of one trip's connecting line, or ``(None, None)`` if degenerate.

    Each trip leaves the previous zone's ring (at that visit's radius) and meets
    this zone's ring, along the line between the two centres. Successive trips on
    the same route are shifted perpendicular to it by :func:`_ribbon_offset`, so
    repeated trips fan out into a ribbon that widens with the route's traffic
    instead of stacking on a single line.
    """
    no_line = (None, None)
    delta_x = center[0] - last_center[0]
    delta_y = center[1] - last_center[1]
    distance = math.hypot(delta_x, delta_y)
    if distance == 0:
        return no_line

    unit_x = delta_x / distance
    unit_y = delta_y / distance
    # Clamp ring radii so the two endpoints can never cross past each other on
    # very close zones.
    reach = distance * 0.45
    start_reach = min(last_radius, reach)
    end_reach = min(radius, reach)

    # A perpendicular fixed to the route (independent of travel direction) keeps
    # both directions of travel on the same ribbon.
    perp_x, perp_y = _route_perpendicular(last_center, center)
    offset = _ribbon_offset(trip_index, trip_total)

    start = (
        last_center[0] + unit_x * start_reach + perp_x * offset,
        last_center[1] + unit_y * start_reach + perp_y * offset,
    )
    end = (
        center[0] - unit_x * end_reach + perp_x * offset,
        center[1] - unit_y * end_reach + perp_y * offset,
    )
    return (start, end)


def _route_perpendicular(center_a, center_b):
    """Unit vector perpendicular to a route, fixed regardless of travel direction.

    The two endpoints are ordered canonically before taking the perpendicular so
    that A->B and B->A trips share one ribbon rather than splaying to opposite
    sides.
    """
    low, high = sorted((center_a, center_b))
    delta_x = high[0] - low[0]
    delta_y = high[1] - low[1]
    distance = math.hypot(delta_x, delta_y)
    if distance == 0:
        return (0.0, 0.0)
    return (-delta_y / distance, delta_x / distance)


def _ribbon_offset(trip_index, trip_total):
    """Perpendicular shift for one trip so a route's trips spread into a ribbon.

    Trips are centred on the route and spaced ``RIBBON_STEP`` apart, but the
    whole ribbon is capped at ``MAX_RIBBON_HALF_WIDTH`` either side; busier
    routes pack more trips into that capped width.
    """
    if trip_total <= 1:
        return 0.0
    step = eq_display.RIBBON_STEP
    full_width = (trip_total - 1) * step
    max_width = 2 * eq_display.MAX_RIBBON_HALF_WIDTH
    if full_width > max_width:
        step = max_width / (trip_total - 1)
    return (trip_index - (trip_total - 1) / 2) * step


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
