import map_path

# Synthetic centres far enough apart that the rings never overlap, so the
# connecting-line geometry stays exact and easy to reason about.
TEST_RADIUS = 12.0
TEST_CENTERS = {
    "Grobb": (0.0, 0.0),
    "Innothule Swamp": (100.0, 0.0),
    "Great Divide": (0.0, 200.0),
}


def _patch_geometry(monkeypatch):
    monkeypatch.setattr(map_path.eq_display, "MAX_RING_RADIUS", TEST_RADIUS)
    # Disable the minimum-radius floor so the area-proportional maths stays
    # exact; the floor has its own dedicated test below.
    monkeypatch.setattr(map_path.eq_display, "MIN_RING_RADIUS", 0.0)
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


def test_build_map_events_attaches_line_to_matching_ring_radius(monkeypatch):
    _patch_geometry(monkeypatch)

    # Both zones visited twice => equally busy => both full radius 12, with an
    # inner ring at 6. The third move (back to Grobb) leaves Innothule's inner
    # ring (radius 6) and arrives at Grobb's outer ring (radius 12).
    events = map_path.build_map_events(
        ["Grobb", "Innothule Swamp", "Grobb", "Innothule Swamp"]
    )

    return_trip = events[2]
    assert return_trip.line_start == (94.0, 0.0)
    assert return_trip.line_end == (12.0, 0.0)


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
