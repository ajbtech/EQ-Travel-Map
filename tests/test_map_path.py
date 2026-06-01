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


def test_build_map_events_stacks_repeat_visits_into_concentric_rings(monkeypatch):
    _patch_geometry(monkeypatch)

    events = map_path.build_map_events(["Grobb", "Innothule Swamp", "Grobb"])

    radii = [(event.center, event.radius) for event in events]
    # Grobb is visited twice: an inner ring first, the full-radius ring last.
    assert radii == [
        ((0.0, 0.0), 6.0),
        ((100.0, 0.0), 12.0),
        ((0.0, 0.0), 12.0),
    ]


def test_build_map_events_colours_visits_chronologically(monkeypatch):
    _patch_geometry(monkeypatch)

    events = map_path.build_map_events(["Grobb", "Innothule Swamp", "Grobb"])

    # First visit is red (0.0), last is violet (1.0), evenly spaced between.
    assert [event.percent for event in events] == [0.0, 0.5, 1.0]


def test_build_map_events_attaches_line_to_matching_ring_radius(monkeypatch):
    _patch_geometry(monkeypatch)

    events = map_path.build_map_events(["Grobb", "Innothule Swamp", "Grobb"])

    # The return trip leaves Innothule's full ring and arrives at Grobb's
    # outer (second-visit) ring, both at radius 12 along the shared axis.
    return_trip = events[2]
    assert return_trip.line_start == (88.0, 0.0)
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
