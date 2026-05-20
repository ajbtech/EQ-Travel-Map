from datetime import datetime

import line_reader
import log_parser


def test_parse_character_logs_with_no_matching_files_returns_empty_summary(tmp_path):
    _, zone_list, summary = log_parser.parse_character_logs(tmp_path, "Missing")

    assert zone_list.get_raw_eq_list() == []
    assert summary.line_count == 0
    assert summary.current_level == 1


def test_parse_log_files_ignores_empty_files_mixed_with_real_files(tmp_path):
    empty_log = tmp_path / "ARCHIVEeqlog_Gorrek_P1999Green.txt"
    real_log = tmp_path / "ARCHIVE2eqlog_Gorrek_P1999Green.txt"
    empty_log.write_text("")
    real_log.write_text(
        "[Sat Sep 24 19:51:48 2022] Welcome to EverQuest!\n"
        "[Sun Jan 08 15:01:29 2023] You have entered Lake Rathetear.\n"
    )

    _, zone_list, summary = log_parser.parse_log_files([empty_log, real_log])

    assert summary.line_count == 2
    assert summary.login_count == 1
    assert zone_list.get_raw_eq_list() == ["Lake Rathetear"]


def test_get_first_log_timestamp_returns_max_when_file_has_no_timestamp(tmp_path):
    log_file = tmp_path / "eqlog_Gorrek_P1999Green.txt"
    log_file.write_text("This line has no timestamp.\n")

    assert log_parser.get_first_log_timestamp(log_file) == datetime.max


def test_parse_log_lines_tracks_first_login_and_most_recent_message():
    lines = [
        "[Sat Sep 24 19:51:48 2022] Welcome to EverQuest!",
        "[Sat Sep 24 19:52:00 2022] You have entered Grobb.",
        "[Sat Sep 24 19:53:00 2022] You say, 'hello'",
    ]

    _, _, summary = log_parser.parse_log_lines(lines)

    assert summary.first_login_message == lines[0]
    assert summary.most_recent_message == lines[-1]


def test_parse_log_files_reports_progress(monkeypatch, tmp_path):
    monkeypatch.setattr(log_parser, "PROGRESS_LINE_INTERVAL", 2)
    log_file = tmp_path / "ARCHIVEeqlog_Gorrek_P1999Green.txt"
    log_file.write_text(
        "[Sat Sep 24 19:51:48 2022] Welcome to EverQuest!\n"
        "[Sat Sep 24 19:52:00 2022] You have entered Grobb.\n"
        "[Sat Sep 24 19:53:00 2022] You say, 'hello'\n"
        "[Sat Sep 24 19:54:00 2022] You say, 'still here'\n"
        "[Sat Sep 24 19:55:00 2022] You say, 'done'\n"
    )
    progress_updates = []

    log_parser.parse_log_files([log_file], progress_updates.append)

    assert progress_updates[0] == log_parser.ParseProgress(log_file, 0)
    assert log_parser.ParseProgress(log_file, 2) in progress_updates
    assert log_parser.ParseProgress(log_file, 4) in progress_updates
    assert progress_updates[-1] == log_parser.ParseProgress(log_file, 5)


def test_count_lines_in_files_sums_lines_across_files(tmp_path):
    a = tmp_path / "a.txt"
    b = tmp_path / "b.txt"
    a.write_text("line1\nline2\nline3\n")
    b.write_text("only\n")

    assert log_parser.count_lines_in_files([a, b]) == 4


def test_count_lines_in_files_handles_empty_files(tmp_path):
    empty = tmp_path / "empty.txt"
    empty.write_text("")

    assert log_parser.count_lines_in_files([empty]) == 0


def test_count_lines_in_files_counts_final_line_without_newline(tmp_path):
    log = tmp_path / "no_trailing_newline.txt"
    log.write_text("first\nsecond")

    assert log_parser.count_lines_in_files([log]) == 2


def test_count_lines_in_files_returns_zero_for_no_files():
    assert log_parser.count_lines_in_files([]) == 0


def test_parse_log_lines_tracks_max_damage_per_type():
    lines = [
        "You slash a goblin for 10 points of damage.",
        "You slash a troll for 25 points of damage.",
        "You slash a rat for 5 points of damage.",
        "You backstab a zombie for 80 points of damage.",
    ]
    _, _, summary = log_parser.parse_log_lines(lines)
    assert summary.max_damage["slash"] == 25
    assert summary.max_damage["backstab"] == 80
    assert "pierce" not in summary.max_damage


def test_parse_log_lines_excludes_backstab_over_cap():
    lines = [
        "You backstab a zombie for 80 points of damage.",
        "You backstab a goblin for 32000 points of damage.",
    ]
    _, _, summary = log_parser.parse_log_lines(lines)
    assert summary.max_damage["backstab"] == 80


def test_parse_log_lines_keeps_backstab_at_cap_boundary():
    lines = [
        "You backstab a zombie for 10000 points of damage.",
        "You backstab a goblin for 10001 points of damage.",
    ]
    _, _, summary = log_parser.parse_log_lines(lines)
    assert summary.max_damage["backstab"] == 10000


def test_parse_log_lines_cap_does_not_affect_other_damage_types():
    lines = [
        "You slash a goblin for 32000 points of damage.",
    ]
    _, _, summary = log_parser.parse_log_lines(lines)
    assert summary.max_damage["slash"] == 32000


def test_parse_log_lines_counts_jboot_clicks():
    lines = [
        "[Sun Apr 20 13:15:27 2025] Your feet feel quick.",
        "[Sun Apr 20 13:16:27 2025] Your feet feel quick.",
        "[Sun Apr 20 13:17:27 2025] You have entered Grobb.",
    ]
    _, _, summary = log_parser.parse_log_lines(lines)
    assert summary.jboot_click_count == 2


def test_parse_log_lines_counts_alcohol_and_intoxication():
    lines = [
        "[Wed May 20 06:05:09 2026] Glug, glug, glug...  You take a swig of ale.",
        "[Wed May 20 06:05:10 2026] Glug, glug, glug...  You take a swig of ale.",
        (
            "[Wed May 20 06:05:12 2026] You could not possibly consume more "
            "alcohol or become more intoxicated!"
        ),
    ]
    _, _, summary = log_parser.parse_log_lines(lines)
    assert summary.alcohol_count == 2
    assert summary.totally_intoxicated_count == 1


def test_parse_log_lines_trivia_counts_zero_when_absent():
    lines = [
        "[Sat Sep 24 19:51:48 2022] Welcome to EverQuest!",
        "[Sun Jan 08 15:01:29 2023] You have entered Lake Rathetear.",
    ]
    _, _, summary = log_parser.parse_log_lines(lines)
    assert summary.jboot_click_count == 0
    assert summary.alcohol_count == 0
    assert summary.totally_intoxicated_count == 0


def test_build_empty_summary_has_zero_trivia_counts():
    summary = log_parser.build_empty_summary()
    assert summary.jboot_click_count == 0
    assert summary.alcohol_count == 0
    assert summary.totally_intoxicated_count == 0


def test_parse_log_lines_tracks_spell_damage():
    lines = [
        "You hit a goblin for 30 points of non-melee damage.",
        "You hit an orc for 99 points of non-melee damage.",
    ]
    _, _, summary = log_parser.parse_log_lines(lines)
    assert summary.max_damage["spell"] == 99


def test_parse_log_lines_empty_max_damage_when_no_damage_lines():
    lines = [
        "[Sat Sep 24 19:51:48 2022] Welcome to EverQuest!",
        "[Sun Jan 08 15:01:29 2023] You have entered Lake Rathetear.",
    ]
    _, _, summary = log_parser.parse_log_lines(lines)
    assert summary.max_damage == {}


def test_build_empty_summary_has_empty_max_damage():
    summary = log_parser.build_empty_summary()
    assert summary.max_damage == {}


def test_parse_log_lines_tracks_spell_casts():
    lines = [
        "[Sat Sep 24 20:30:45 2022] You begin casting Spirit of Wolf.",
        "[Sat Sep 24 20:31:00 2022] You begin casting Haste.",
        "[Sat Sep 24 20:31:30 2022] You begin casting Spirit of Wolf.",
    ]
    _, _, summary = log_parser.parse_log_lines(lines)
    top = summary.spell_list.get_count_alpha_sorted_eq_list()
    assert ("Spirit of Wolf", 2) in top
    assert ("Haste", 1) in top


def test_parse_log_lines_empty_spell_list_when_no_casts():
    lines = [
        "[Sat Sep 24 19:51:48 2022] Welcome to EverQuest!",
        "[Sun Jan 08 15:01:29 2023] You have entered Lake Rathetear.",
    ]
    _, _, summary = log_parser.parse_log_lines(lines)
    assert summary.spell_list.get_raw_eq_list() == []


def test_build_empty_summary_has_empty_spell_list():
    summary = log_parser.build_empty_summary()
    assert summary.spell_list.get_raw_eq_list() == []


def test_build_empty_summary_has_empty_timeline():
    summary = log_parser.build_empty_summary()
    assert summary.timeline == []


def test_timeline_records_events_in_order():
    # Four leading non-event lines so the add_starting_zones special case
    # (which captures a zone from the first four lines before login filtering)
    # doesn't reorder the sequence under test.
    lines = [
        "[Sat Sep 24 19:50:00 2022] You say, 'one'",
        "[Sat Sep 24 19:50:10 2022] You say, 'two'",
        "[Sat Sep 24 19:50:20 2022] You say, 'three'",
        "[Sat Sep 24 19:50:30 2022] You say, 'four'",
        "[Sat Sep 24 19:51:48 2022] Welcome to EverQuest!",
        "[Sat Sep 24 19:51:55 2022] You say, 'hi'",
        "[Sat Sep 24 19:52:00 2022] You have entered Grobb.",
        "[Sat Sep 24 19:53:00 2022] You have slain a froglok!",
        "[Sat Sep 24 19:54:00 2022] You have gained a level! Welcome to level 2!",
        "[Sat Sep 24 19:55:00 2022] You have been slain by a froglok!",
    ]
    _, _, summary = log_parser.parse_log_lines(lines)
    kinds = [event.kind for event in summary.timeline]
    assert kinds == [
        line_reader.EventType.LOGIN,
        line_reader.EventType.ZONE,
        line_reader.EventType.KILL,
        line_reader.EventType.LEVEL_GAINED,
        line_reader.EventType.DEATH,
    ]


def test_timeline_zone_entries_match_zone_list():
    lines = [
        "[Sat Sep 24 19:51:48 2022] You have entered Grobb.",
        "[Sat Sep 24 19:52:00 2022] You have entered Innothule Swamp.",
        "[Sat Sep 24 19:53:00 2022] You have entered Grobb.",
    ]
    _, zone_list, summary = log_parser.parse_log_lines(lines)
    zone_values = [
        event.value
        for event in summary.timeline
        if event.kind == line_reader.EventType.ZONE
    ]
    assert zone_values == zone_list.get_raw_eq_list()


def test_timeline_excludes_player_damage_and_spell():
    lines = [
        "[Sat Sep 24 19:51:48 2022] You begin casting Spirit of Wolf.",
        "[Sat Sep 24 19:52:00 2022] You slash a goblin for 10 points of damage.",
        "[Sat Sep 24 19:53:00 2022] You have slain a goblin!",
    ]
    _, _, summary = log_parser.parse_log_lines(lines)
    kinds = [event.kind for event in summary.timeline]
    assert line_reader.EventType.SPELL_CAST not in kinds
    assert line_reader.EventType.PLAYER_DAMAGE not in kinds
    assert kinds == [line_reader.EventType.KILL]
