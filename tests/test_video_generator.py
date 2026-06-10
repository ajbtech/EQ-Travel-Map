import eq_display
import log_parser
import video_generator


def _summary_and_zones(lines):
    _, zone_list, summary = log_parser.parse_log_lines(lines)
    return zone_list, summary


def _kill_count_from_stats(stats_lines):
    for line in stats_lines:
        if line.startswith("Kill Count: "):
            return int(line[len("Kill Count: ") :].replace(",", ""))
    raise AssertionError("no Kill Count line")


def test_empty_timeline_yields_one_base_frame():
    zone_list, summary = _summary_and_zones([])
    gen = video_generator.VideoGenerator("Gorrek", zone_list, summary)

    assert gen.total_frames() == 1
    frames = list(gen.frames())
    assert len(frames) == 1
    assert frames[0].map_image is not None


def test_total_frames_capped_by_duration():
    lines = [f"[ts] You have slain mob{i}!" for i in range(20)]
    zone_list, summary = _summary_and_zones(lines)
    gen = video_generator.VideoGenerator(
        "Gorrek", zone_list, summary, target_seconds=2, fps=2
    )

    # 20 events, 2s * 2fps = 4 frames cap.
    assert gen.total_frames() == 4
    assert len(list(gen.frames())) == 4


def test_total_frames_equals_event_count_when_few_events():
    lines = [f"[ts] You have slain mob{i}!" for i in range(3)]
    zone_list, summary = _summary_and_zones(lines)
    gen = video_generator.VideoGenerator(
        "Gorrek", zone_list, summary, target_seconds=120, fps=24
    )

    assert gen.total_frames() == 3


def test_kill_count_non_decreasing_and_reaches_total():
    lines = [f"[ts] You have slain mob{i}!" for i in range(10)]
    zone_list, summary = _summary_and_zones(lines)
    gen = video_generator.VideoGenerator(
        "Gorrek", zone_list, summary, target_seconds=1, fps=5
    )

    counts = [_kill_count_from_stats(f.stats_lines) for f in gen.frames()]
    assert counts == sorted(counts)
    assert counts[-1] == 10


def test_top_kills_lines_ordered_by_count():
    lines = (
        ["[ts] You have slain orc!"] * 3
        + ["[ts] You have slain rat!"] * 1
        + ["[ts] You have slain goblin!"] * 2
    )
    zone_list, summary = _summary_and_zones(lines)
    gen = video_generator.VideoGenerator(
        "Gorrek", zone_list, summary, target_seconds=1, fps=1
    )

    final = list(gen.frames())[-1]
    assert final.top_kills_lines[0] == "Top 5 killed creatures:"
    assert final.top_kills_lines[1] == "1. orc: 3"
    assert final.top_kills_lines[2] == "2. goblin: 2"
    assert final.top_kills_lines[3] == "3. rat: 1"


def test_final_frame_map_matches_full_reverse_render():
    lines = [
        "[ts] You say, 'x'",
        "[ts] You say, 'x'",
        "[ts] You say, 'x'",
        "[ts] You say, 'x'",
        "[ts] You have entered Grobb.",
        "[ts] You have entered Innothule Swamp.",
        "[ts] You have entered Grobb.",
    ]
    zone_list, summary = _summary_and_zones(lines)
    gen = video_generator.VideoGenerator(
        "Gorrek", zone_list, summary, target_seconds=1, fps=2
    )

    frames = list(gen.frames())

    reference = eq_display.MapRenderer()
    # Match the renderer's two-pass order: every disc first, then every line.
    for event in reversed(gen._all_map_events):
        event.draw_disc(reference)
    for event in reversed(gen._all_map_events):
        event.draw_line(reference)
    last_zone = "Grobb"
    if gen._all_map_events:
        loc = eq_display.get_zone_center(last_zone)
        reference.draw_location_circle(loc, gen._all_map_events[-1].percent)

    assert frames[-1].map_image.tobytes() == reference.get_image().tobytes()


def test_video_frame_map_has_circle_at_last_zone_center():
    lines = [
        "[ts] You have entered Grobb.",
        "[ts] You have entered Innothule Swamp.",
    ]
    zone_list, summary = _summary_and_zones(lines)
    gen = video_generator.VideoGenerator(
        "Gorrek", zone_list, summary, target_seconds=1, fps=2
    )
    frames = list(gen.frames())
    final_map = frames[-1].map_image

    x, y = eq_display.get_zone_center("Innothule Swamp")
    r = eq_display.LOCATION_CIRCLE_RADIUS
    top_pixel = final_map.getpixel((int(x), int(y) - r))
    percent = gen._all_map_events[-1].percent
    expected = eq_display._to_rgba(eq_display.make_rainbow(percent))
    assert top_pixel == expected


def test_map_updated_is_false_for_kill_only_frames():
    lines = ["[ts] You have slain a frog!"] * 10
    zone_list, summary = _summary_and_zones(lines)
    gen = video_generator.VideoGenerator(
        "Gorrek", zone_list, summary, target_seconds=1, fps=5
    )
    frames = list(gen.frames())
    # No zone transitions means no map updates.
    assert all(not f.map_updated for f in frames)


def test_map_updated_is_true_when_zone_transition_occurs():
    lines = [
        "[ts] You have entered Grobb.",
        "[ts] You have entered Innothule Swamp.",
    ]
    zone_list, summary = _summary_and_zones(lines)
    gen = video_generator.VideoGenerator(
        "Gorrek", zone_list, summary, target_seconds=1, fps=2
    )
    frames = list(gen.frames())
    # Zone transitions must mark at least one frame as map_updated.
    assert any(f.map_updated for f in frames)


def test_content_version_is_non_decreasing():
    lines = [f"[ts] You have slain mob{i}!" for i in range(5)]
    zone_list, summary = _summary_and_zones(lines)
    gen = video_generator.VideoGenerator(
        "Gorrek", zone_list, summary, target_seconds=1, fps=5
    )
    versions = [f.content_version for f in gen.frames()]
    assert versions == sorted(versions)


def test_content_version_stable_when_no_new_events():
    lines = ["[ts] You have slain a mob!"]
    zone_list, summary = _summary_and_zones(lines)
    # More frames than events means some frames will have identical content.
    gen = video_generator.VideoGenerator(
        "Gorrek", zone_list, summary, target_seconds=10, fps=24
    )
    versions = [f.content_version for f in gen.frames()]
    unique_versions = len(set(versions))
    # Only one event → at most two distinct versions (before and after the event).
    assert unique_versions <= 2


def test_frames_is_safe_to_call_twice():
    lines = [
        "[ts] You have entered Grobb.",
        "[ts] You have entered Innothule Swamp.",
    ]
    zone_list, summary = _summary_and_zones(lines)
    gen = video_generator.VideoGenerator(
        "Gorrek", zone_list, summary, target_seconds=1, fps=2
    )
    frames_a = list(gen.frames())
    frames_b = list(gen.frames())
    assert frames_a[-1].map_image.tobytes() == frames_b[-1].map_image.tobytes()
