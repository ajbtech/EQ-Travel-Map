import map_path


def test_build_map_events_draws_adjacent_transition(monkeypatch):
    monkeypatch.setattr(
        map_path.eq_display,
        "get_shifted_zone_center",
        lambda zone, visit_number, total_visits: [zone, visit_number, total_visits],
    )

    events = map_path.build_map_events(["Grobb", "Innothule Swamp"])

    assert events == [
        map_path.MapLine(
            start_loc=["Grobb", 1, 1],
            end_loc=["Innothule Swamp", 1, 1],
            percent=0,
        )
    ]


def test_build_map_events_marks_skipped_transition_destination(monkeypatch):
    monkeypatch.setattr(
        map_path.eq_display,
        "get_shifted_zone_center",
        lambda zone, visit_number, total_visits: [zone, visit_number, total_visits],
    )

    events = map_path.build_map_events(["Grobb", "Great Divide"])

    assert events == [
        map_path.MapDot(
            loc=["Great Divide", 1, 1],
            percent=0,
        )
    ]


def test_build_map_events_uses_chronological_visit_count_for_jitter(monkeypatch):
    visits = []

    def fake_get_shifted_zone_center(zone, visit_number, total_visits):
        visits.append((zone, visit_number, total_visits))
        return [zone, visit_number, total_visits]

    monkeypatch.setattr(
        map_path.eq_display,
        "get_shifted_zone_center",
        fake_get_shifted_zone_center,
    )

    map_path.build_map_events(["Grobb", "Innothule Swamp", "Grobb"])

    assert visits == [
        ("Grobb", 1, 2),
        ("Innothule Swamp", 1, 1),
        ("Grobb", 2, 2),
    ]


def test_build_map_events_jitters_repeated_skipped_destinations(monkeypatch):
    visits = []

    def fake_get_shifted_zone_center(zone, visit_number, total_visits):
        visits.append((zone, visit_number, total_visits))
        return [zone, visit_number, total_visits]

    monkeypatch.setattr(
        map_path.eq_display,
        "get_shifted_zone_center",
        fake_get_shifted_zone_center,
    )

    events = map_path.build_map_events(["Grobb", "Great Divide", "Grobb"])

    assert visits == [
        ("Grobb", 1, 2),
        ("Great Divide", 1, 1),
        ("Grobb", 2, 2),
    ]
    assert events[-1] == map_path.MapDot(["Grobb", 2, 2], 1 / 3)


def test_get_known_zones_filters_unknown_zones():
    zones = map_path.get_known_zones(["Grobb", "Definitely Unknown Zone"])

    assert zones == ["Grobb"]
