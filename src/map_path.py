import math
from collections import Counter
from dataclasses import dataclass

import eq_display
import zone_graph


@dataclass(frozen=True)
class ZoneVisit:
    """One visit to a known zone, drawn as a colour ring over a link trapezoid.

    Each visit paints a filled disc centred on the zone. A zone's visits stack
    into concentric discs: the first visit is the small inner disc and the last
    visit is the full-radius outer disc, so the ring colour runs from the
    earliest visit's rainbow colour at the centre to the latest at the edge.
    The zone's outer radius scales with how often it was visited — its disc
    *area* is proportional to its visit count relative to the busiest zone, so
    the most-visited zone fills ``MAX_RING_RADIUS`` and the rest shrink from
    there.

    When the move from the previous zone is graph-adjacent, ``trapezoid`` holds
    the four corners of a band that connects the two circles: it meets each
    circle at this visit's ring radius (so its colour lines up with the matching
    ring) and spans the full width there. Drawn beneath the discs, successive
    trips between the same zones nest outward as the rings grow and fill the gap
    with chronological colour stripes.
    """

    center: tuple[float, float]
    radius: float
    percent: float
    trapezoid: tuple[tuple[float, float], ...] | None = None

    def draw_disc(self, renderer):
        renderer.draw_disc(self.center, self.radius, percent=self.percent)

    def draw_trapezoid(self, renderer):
        if self.trapezoid is not None:
            renderer.draw_trapezoid(self.trapezoid, percent=self.percent)

    def draw(self, renderer):
        # Trapezoid first, then the disc on top, so the linking band sits beneath
        # the zone's filled circle.
        self.draw_trapezoid(renderer)
        self.draw_disc(renderer)


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
        zone_total = zone_total_counts[zone]
        radius = _visit_radius(zone_visit_counts[zone], zone_total, max_total)
        center = eq_display.get_zone_center(zone)

        if last_zone != "" and zone_graph.are_adjacent(last_zone, zone):
            trapezoid = _transition_trapezoid(last_center, last_radius, center, radius)
        else:
            trapezoid = None
        draw_events.append(ZoneVisit(center, radius, percent, trapezoid))

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


def _transition_trapezoid(last_center, last_radius, center, radius):
    """Four corners of the band linking two zones, or ``None`` if degenerate.

    The band meets the previous zone's circle across a chord of half-width
    ``last_radius`` and this zone's circle across a chord of half-width
    ``radius`` — both this visit's ring radius — laid perpendicular to the route
    between the centres. Because each end uses the matching ring radius, later
    trips (larger rings) produce wider bands that nest over earlier ones, and
    the widest reaches the full circle diameter.
    """
    perp_x, perp_y = _route_perpendicular(last_center, center)
    if (perp_x, perp_y) == (0.0, 0.0):
        return None

    start_top = (
        last_center[0] + perp_x * last_radius,
        last_center[1] + perp_y * last_radius,
    )
    start_bottom = (
        last_center[0] - perp_x * last_radius,
        last_center[1] - perp_y * last_radius,
    )
    end_top = (center[0] + perp_x * radius, center[1] + perp_y * radius)
    end_bottom = (center[0] - perp_x * radius, center[1] - perp_y * radius)
    return (start_top, end_top, end_bottom, start_bottom)


def _route_perpendicular(center_a, center_b):
    """Unit vector perpendicular to a route, fixed regardless of travel direction.

    The two endpoints are ordered canonically before taking the perpendicular so
    that A->B and B->A trips build the same band rather than mirrored ones.
    """
    low, high = sorted((center_a, center_b))
    delta_x = high[0] - low[0]
    delta_y = high[1] - low[1]
    distance = math.hypot(delta_x, delta_y)
    if distance == 0:
        return (0.0, 0.0)
    return (-delta_y / distance, delta_x / distance)


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
