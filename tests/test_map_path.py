import map_path

# Synthetic centres far enough apart that the rings never overlap, so the
# connecting-line geometry stays exact and easy to reason about.
TEST_RADIUS = 12.0
TEST_CENTERS = {
    "Grobb": (0.0, 0.0),
    "Innothule Swamp": (100.0, 0.0),
    "Great Divide": (0.0, 200.0),
}


def _patch_geometry(monkeypatch, ribbon_step=0.0):
    monkeypatch.setattr(map_path.eq_display, "MAX_RING_RADIUS", TEST_RADIUS)
    # Disable the minimum-radius floor so the area-proportional maths stays
    # exact; the floor has its own dedicated test below.
    monkeypatch.setattr(map_path.eq_display, "MIN_RING_RADIUS", 0.0)
    # Default the ribbon spread off so single-trip geometry stays exact; tests
    # that exercise the fan set their own step and cap.
    monkeypatch.setattr(map_path.eq_display, "RIBBON_STEP", ribbon_step)
    monkeypatch.setattr(map_path.eq_display, "MAX_RIBBON_HALF_WIDTH", 1000.0)
    monkeypatch.setattr(
        map_path.eq_display, "get_zone_center", lambda zone: TEST_CENTERS[zone]
    )


def test_build_map_events_draws_adjacent_transition(monkeypatch):
    _patch_geometry(monkeypatch)

    events = map_path.build_map_events(["Grobb", "Innothule Swamp"])

    assert events == [
        map_path.ZoneVisit((0.0, 0.0), 12.0, 0.0, None, None),
        map_path.ZoneVisit(
            (100.0, 0.0),
            12.0,
            1.0,
            line_start=(12.0, 0.0),
            line_end=(88.0, 0.0),
        ),
    ]


def test_build_map_events_skips_line_for_non_adjacent_transition(monkeypatch):
    _patch_geometry(monkeypatch)

    events = map_path.build_map_events(["Grobb", "Great Divide"])

    assert events[1].line_start is None
    assert events[1].line_end is None
    assert events[1].center == (0.0, 200.0)


def test_build_map_events_outer_radius_is_area_proportional_to_busiest_zone(
    monkeypatch,
):
    _patch_geometry(monkeypatch)

    # Grobb visited 4x is the busiest (full radius); Innothule visited once has
    # a quarter of the visits, so a quarter of the area => half the radius.
    events = map_path.build_map_events(
        ["Grobb", "Grobb", "Grobb", "Grobb", "Innothule Swamp"]
    )

    grobb_radii = [event.radius for event in events if event.center == (0.0, 0.0)]
    innothule_radii = [event.radius for event in events if event.center == (100.0, 0.0)]
    # Grobb's four visits stack as evenly spaced concentric rings out to 12.
    assert grobb_radii == [3.0, 6.0, 9.0, 12.0]
    assert innothule_radii == [6.0]


def test_build_map_events_floors_outer_radius_at_minimum(monkeypatch):
    monkeypatch.setattr(map_path.eq_display, "MAX_RING_RADIUS", TEST_RADIUS)
    monkeypatch.setattr(map_path.eq_display, "MIN_RING_RADIUS", 5.0)
    monkeypatch.setattr(
        map_path.eq_display, "get_zone_center", lambda zone: TEST_CENTERS[zone]
    )

    # Grobb visited 16x is busiest (radius 12). Innothule's single visit would
    # area-scale to 12 * sqrt(1/16) = 3.0, below the 5.0 floor, so it is
    # clamped up to keep the zone visible.
    events = map_path.build_map_events(["Grobb"] * 16 + ["Innothule Swamp"])

    innothule_radius = next(
        event.radius for event in events if event.center == (100.0, 0.0)
    )
    assert innothule_radius == 5.0


def test_build_map_events_colours_visits_chronologically(monkeypatch):
    _patch_geometry(monkeypatch)

    events = map_path.build_map_events(["Grobb", "Innothule Swamp", "Grobb"])

    # First visit is red (0.0), last is violet (1.0), evenly spaced between.
    assert [event.percent for event in events] == [0.0, 0.5, 1.0]


def test_build_map_events_attaches_line_to_each_visits_ring_radius(monkeypatch):
    _patch_geometry(monkeypatch)

    # Innothule visited once (outer radius 6 => its single ring at radius 6);
    # Grobb four times (outer radius 12 => first-visit ring at radius 3). The
    # one trip leaves Innothule's ring and meets Grobb's first-visit ring.
    events = map_path.build_map_events(
        ["Innothule Swamp", "Grobb", "Grobb", "Grobb", "Grobb"]
    )

    first_move = events[1]
    assert first_move.line_start == (94.0, 0.0)
    assert first_move.line_end == (3.0, 0.0)


def test_build_map_events_fans_repeat_trips_into_a_ribbon(monkeypatch):
    _patch_geometry(monkeypatch, ribbon_step=10.0)

    # Three trips on the Grobb<->Innothule route. Both zones visited twice =>
    # rings at radius 6 (first visit) and 12 (second). Trips spread perpendicular
    # to the route (the y axis here) at offsets -10, 0, +10.
    events = map_path.build_map_events(
        ["Grobb", "Innothule Swamp", "Grobb", "Innothule Swamp"]
    )

    trips = [event for event in events if event.line_start is not None]
    offsets = [event.line_start[1] for event in trips]
    assert offsets == [-10.0, 0.0, 10.0]
    # Middle trip sits on the route axis: Grobb 2nd-visit ring (12) to
    # Innothule 1st-visit ring (6).
    assert trips[1].line_start == (94.0, 0.0)
    assert trips[1].line_end == (12.0, 0.0)


def test_build_map_events_omits_line_for_same_zone_revisit(monkeypatch):
    _patch_geometry(monkeypatch)

    events = map_path.build_map_events(["Grobb", "Grobb"])

    assert len(events) == 2
    assert events[1].line_start is None


def test_build_map_events_empty_for_no_known_zones(monkeypatch):
    _patch_geometry(monkeypatch)

    assert map_path.build_map_events(["Definitely Unknown Zone"]) == []


def test_get_known_zones_filters_unknown_zones():
    zones = map_path.get_known_zones(["Grobb", "Definitely Unknown Zone"])

    assert zones == ["Grobb"]


def test_cumulative_event_counts_last_equals_total_events():
    zones = ["Grobb", "Innothule Swamp", "Grobb", "Great Divide"]
    counts = map_path.cumulative_event_counts(zones)

    assert counts[-1] == len(map_path.build_map_events(zones))


def test_cumulative_event_counts_is_nondecreasing():
    zones = ["Grobb", "Great Divide", "Grobb", "Innothule Swamp"]
    counts = map_path.cumulative_event_counts(zones)

    assert all(b >= a for a, b in zip(counts, counts[1:]))


def test_cumulative_event_counts_one_per_known_zone():
    counts = map_path.cumulative_event_counts(
        ["Grobb", "Definitely Unknown Zone", "Innothule Swamp"]
    )

    # Only the two known zones produce entries, one event each.
    assert counts == [1, 2]


def test_cumulative_event_counts_empty_for_no_known_zones():
    assert map_path.cumulative_event_counts(["Definitely Unknown Zone"]) == []
