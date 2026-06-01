import eq_parser
import log_parser
import money_sorter
import summary_formatter
from eq_list import EQList


def test_find_log_files_returns_character_archives_in_chronological_order(tmp_path):
    later_log = tmp_path / "ARCHIVE2eqlog_Gorrek_P1999Green.txt"
    earlier_log = tmp_path / "ARCHIVEeqlog_Gorrek_P1999Green.txt"
    other_character_log = tmp_path / "ARCHIVEeqlog_Other_P1999Green.txt"

    later_log.write_text("[Sat May 11 20:23:18 2024] Logging is on.\n")
    earlier_log.write_text("[Sat Sep 24 19:51:48 2022] Welcome to EverQuest!\n")
    other_character_log.write_text("[Sat Sep 24 19:51:48 2022] Welcome to EverQuest!\n")

    log_files = log_parser.find_log_files(tmp_path, "Gorrek")

    assert log_files == [earlier_log, later_log]


def test_parse_log_files_handles_unexpected_bytes(tmp_path):
    log_file = tmp_path / "ARCHIVEeqlog_Gorrek_P1999Green.txt"
    log_file.write_bytes(b"[Sat Sep 24 19:51:48 2022] odd byte: \x90\n")

    _, _, summary = log_parser.parse_log_files([log_file])

    assert summary.line_count == 1
    assert "odd byte" in summary.most_recent_message


def test_parse_character_logs_combines_matching_files(tmp_path):
    first_log = tmp_path / "ARCHIVEeqlog_Gorrek_P1999Green.txt"
    second_log = tmp_path / "ARCHIVE2eqlog_Gorrek_P1999Green.txt"
    first_log.write_text(
        "[Sat Sep 24 19:51:48 2022] Welcome to EverQuest!\n"
        "[Sun Jan 08 15:01:29 2023] You have entered Lake Rathetear.\n"
    )
    second_log.write_text("[Sat Oct 29 13:05:25 2024] You have slain a ghoul!\n")

    kill_list, zone_list, summary = log_parser.parse_character_logs(tmp_path, "Gorrek")

    assert summary.login_count == 1
    assert summary.zone_count == 1
    assert summary.kill_count == 1
    assert kill_list.get_raw_eq_list() == ["ghoul"]
    assert zone_list.get_raw_eq_list() == ["Lake Rathetear"]


def test_parse_character_logs_counts_starting_zone_in_each_file(tmp_path):
    first_log = tmp_path / "ARCHIVEeqlog_Gorrek_P1999Green.txt"
    second_log = tmp_path / "ARCHIVE2eqlog_Gorrek_P1999Green.txt"
    first_log.write_text(
        "[Sat Sep 24 19:51:48 2022] Welcome to EverQuest!\n"
        "[Sat Sep 24 19:51:48 2022] You have entered Grobb.\n"
    )
    second_log.write_text(
        "[Sat May 11 20:23:18 2024] Welcome to EverQuest!\n"
        "[Sat May 11 20:23:18 2024] You have entered Lake Rathetear.\n"
    )

    _, zone_list, summary = log_parser.parse_character_logs(tmp_path, "Gorrek")

    assert summary.zone_count == 2
    assert zone_list.get_raw_eq_list() == ["Grobb", "Lake Rathetear"]


def test_arg_parser_accepts_character_log_folder_and_output(tmp_path):
    output_path = tmp_path / "my_map.png"

    args = eq_parser.build_arg_parser().parse_args(
        [
            "Mycharacter",
            "--log-folder",
            str(tmp_path),
            "--output",
            str(output_path),
        ],
    )

    assert args.character_name == "Mycharacter"
    assert args.log_folder == tmp_path
    assert args.output == output_path


def test_main_prints_summary_and_draws_map(monkeypatch, capsys, tmp_path):
    kill_list = EQList()
    zone_list = EQList()
    output_path = tmp_path / "map.png"

    summary = log_parser.ParseSummary(
        first_login_message="[Sat Sep 24 19:51:48 2022] Welcome to EverQuest!",
        most_recent_message="[Sat Sep 24 19:52:00 2022] Logging is on.",
        line_count=2,
        login_count=1,
        death_count=0,
        zone_count=0,
        kill_count=0,
        level_count=0,
        level_lost_count=0,
        current_level=1,
        loot_cash_count=0,
        merch_cash_count=0,
        loot_cash=money_sorter.Cash(),
        merch_cash=money_sorter.Cash(),
    )
    drawn_maps = []

    monkeypatch.setattr(
        eq_parser.log_parser,
        "parse_character_logs",
        lambda log_folder_path, character_name: (kill_list, zone_list, summary),
    )
    monkeypatch.setattr(
        eq_parser,
        "draw_zone_path",
        lambda zones, output_path: drawn_maps.append((zones, output_path)),
    )

    eq_parser.main("Gorrek", log_folder_path=tmp_path, output_path=output_path)

    output = capsys.readouterr().out
    assert "Character: Gorrek" in output
    assert "Total logs: 2" in output
    assert drawn_maps == [(zone_list, output_path)]


def test_draw_zone_path_can_save_map(monkeypatch, tmp_path):
    saved_paths = []

    class FakeMapRenderer:
        def __init__(self, *args, **kwargs):
            pass

        def draw_line(self, zone_loc_1, zone_loc_2, percent):
            pass

        def draw_disc(self, center, radius, percent):
            pass

        def mark_zone_x(self, zone_loc):
            pass

        def save_map(self, output_path):
            saved_paths.append(output_path)

        def display_map(self):
            raise AssertionError("display_map should not be called when saving")

    zone_list = EQList()
    zone_list.add("Grobb")
    output_path = tmp_path / "zone_path.png"

    monkeypatch.setattr(eq_parser.eq_display, "MapRenderer", FakeMapRenderer)

    eq_parser.draw_zone_path(zone_list, output_path=output_path)

    assert saved_paths == [output_path]


def test_draw_zone_path_does_not_mark_zone_centers(monkeypatch, tmp_path):
    class FakeMapRenderer:
        def __init__(self, *args, **kwargs):
            pass

        def draw_line(self, zone_loc_1, zone_loc_2, percent):
            pass

        def draw_disc(self, center, radius, percent):
            pass

        def mark_zone_x(self, zone_loc):
            raise AssertionError("zone center X markers should not be drawn")

        def save_map(self, output_path):
            pass

        def display_map(self):
            raise AssertionError("display_map should not be called when saving")

    zone_list = EQList()
    zone_list.add("Grobb")

    monkeypatch.setattr(eq_parser.eq_display, "MapRenderer", FakeMapRenderer)

    eq_parser.draw_zone_path(zone_list, output_path=tmp_path / "zone_path.png")


def test_draw_zone_path_draws_adjacent_graph_transition(monkeypatch, tmp_path):
    drawn_lines = []

    class FakeMapRenderer:
        def __init__(self, *args, **kwargs):
            pass

        def draw_line(self, zone_loc_1, zone_loc_2, percent):
            drawn_lines.append((zone_loc_1, zone_loc_2))

        def draw_disc(self, center, radius, percent):
            pass

        def mark_zone_x(self, zone_loc):
            pass

        def save_map(self, output_path):
            pass

        def display_map(self):
            raise AssertionError("display_map should not be called when saving")

    zone_list = EQList()
    zone_list.add("Grobb")
    zone_list.add("Innothule Swamp")

    monkeypatch.setattr(eq_parser.eq_display, "MapRenderer", FakeMapRenderer)

    eq_parser.draw_zone_path(zone_list, output_path=tmp_path / "zone_path.png")

    assert len(drawn_lines) == 1


def test_draw_zone_path_draws_newer_segments_first(monkeypatch, tmp_path):
    line_percents = []

    class FakeMapRenderer:
        def __init__(self, *args, **kwargs):
            pass

        def draw_line(self, zone_loc_1, zone_loc_2, percent):
            line_percents.append(percent)

        def draw_disc(self, center, radius, percent):
            pass

        def save_map(self, output_path):
            pass

        def display_map(self):
            raise AssertionError("display_map should not be called when saving")

    zone_list = EQList()
    zone_list.add("Grobb")
    zone_list.add("Innothule Swamp")
    zone_list.add("Southern Desert of Ro")

    monkeypatch.setattr(eq_parser.eq_display, "MapRenderer", FakeMapRenderer)

    eq_parser.draw_zone_path(zone_list, output_path=tmp_path / "zone_path.png")

    # Newest segment (highest chronological percent) is drawn first so older
    # routes remain on top.
    assert line_percents == [1.0, 0.5]


def test_draw_zone_path_draws_a_disc_for_every_known_visit(
    monkeypatch,
    tmp_path,
):
    drawn_discs = []

    class FakeMapRenderer:
        def __init__(self, *args, **kwargs):
            pass

        def draw_line(self, zone_loc_1, zone_loc_2, percent):
            pass

        def draw_disc(self, center, radius, percent):
            drawn_discs.append((center, percent))

        def save_map(self, output_path):
            pass

        def display_map(self):
            raise AssertionError("display_map should not be called when saving")

    zone_list = EQList()
    zone_list.add("Grobb")
    zone_list.add("Innothule Swamp")
    zone_list.add("Grobb")

    monkeypatch.setattr(eq_parser.eq_display, "MapRenderer", FakeMapRenderer)

    eq_parser.draw_zone_path(zone_list, output_path=tmp_path / "zone_path.png")

    # One disc per visit, drawn newest-first so the earliest ring lands on top.
    assert [percent for _, percent in drawn_discs] == [1.0, 0.5, 0.0]


def test_draw_zone_path_skips_non_adjacent_graph_transition(monkeypatch, tmp_path):
    drawn_lines = []

    class FakeMapRenderer:
        def __init__(self, *args, **kwargs):
            pass

        def draw_line(self, zone_loc_1, zone_loc_2, percent):
            drawn_lines.append((zone_loc_1, zone_loc_2))

        def draw_disc(self, center, radius, percent):
            pass

        def mark_zone_x(self, zone_loc):
            pass

        def save_map(self, output_path):
            pass

        def display_map(self):
            raise AssertionError("display_map should not be called when saving")

    zone_list = EQList()
    zone_list.add("Grobb")
    zone_list.add("Great Divide")

    monkeypatch.setattr(eq_parser.eq_display, "MapRenderer", FakeMapRenderer)

    eq_parser.draw_zone_path(zone_list, output_path=tmp_path / "zone_path.png")

    assert drawn_lines == []


def test_draw_zone_path_marks_skipped_transition_destination(
    monkeypatch,
    tmp_path,
    capsys,
):
    drawn_discs = []

    class FakeMapRenderer:
        def __init__(self, *args, **kwargs):
            pass

        def draw_line(self, zone_loc_1, zone_loc_2, percent):
            raise AssertionError("skipped graph transitions should not draw lines")

        def draw_disc(self, center, radius, percent):
            drawn_discs.append(center)

        def save_map(self, output_path):
            pass

        def display_map(self):
            raise AssertionError("display_map should not be called when saving")

    zone_list = EQList()
    zone_list.add("Grobb")
    zone_list.add("Great Divide")

    monkeypatch.setattr(eq_parser.eq_display, "MapRenderer", FakeMapRenderer)

    eq_parser.draw_zone_path(zone_list, output_path=tmp_path / "zone_path.png")

    # No connecting line, but the destination still gets its own colour ring.
    expected_centers = {
        eq_parser.eq_display.get_zone_center("Grobb"),
        eq_parser.eq_display.get_zone_center("Great Divide"),
    }
    assert set(drawn_discs) == expected_centers
    assert "Graph skip" not in capsys.readouterr().out


def test_draw_zone_path_with_no_zones_does_not_crash():
    zone_list = EQList()

    eq_parser.draw_zone_path(zone_list)


def test_draw_zone_path_skips_unknown_zones():
    zone_list = EQList()
    zone_list.add("Definitely Unknown Zone")

    eq_parser.draw_zone_path(zone_list)


def test_parser_returns_summary_counts():
    lines = [
        "[Sat Sep 24 19:51:48 2022] Welcome to EverQuest!",
        "[Sun Jan 08 15:01:29 2023] You have entered Lake Rathetear.",
        "[Sat Oct 29 13:05:25 2022] You have slain a ghoul!",
    ]

    kill_list, zone_list, summary = log_parser.parse_log_lines(lines)

    assert summary.login_count == 1
    assert summary.zone_count == 1
    assert summary.kill_count == 1
    assert kill_list.get_raw_eq_list() == ["ghoul"]
    assert zone_list.get_raw_eq_list() == ["Lake Rathetear"]


def test_parser_handles_empty_log():
    kill_list, zone_list, summary = log_parser.parse_log_lines([])

    assert kill_list.get_raw_eq_list() == []
    assert zone_list.get_raw_eq_list() == []
    assert summary.line_count == 0
    assert summary.login_count == 0
    assert summary.zone_count == 0
    assert summary.current_level == 1


def test_parser_counts_deaths_levels_and_level_loss():
    lines = [
        "[Sun Jan 08 14:50:01 2023] You have gained a level! Welcome to level 2!",
        "[Thu Oct 27 21:01:18 2022] You LOST a level! You are now level 1!",
        "[Sat Sep 24 20:41:47 2022] You have been slain by a froglok!",
    ]

    _, _, summary = log_parser.parse_log_lines(lines)

    assert summary.level_count == 1
    assert summary.level_lost_count == 1
    assert summary.current_level == 1
    assert summary.death_count == 1


def test_parser_uses_most_recent_level_event_as_current_level():
    lines = [
        "[Sun Jan 08 14:50:01 2023] You have gained a level! Welcome to level 37!",
        "[Thu Oct 27 21:01:18 2022] You LOST a level! You are now level 36!",
        "[Thu Oct 27 21:05:18 2022] You have gained a level! Welcome to level 37!",
    ]

    _, _, summary = log_parser.parse_log_lines(lines)

    assert summary.level_count == 2
    assert summary.level_lost_count == 1
    assert summary.current_level == 37


def test_parser_summarizes_loot_and_merchant_cash():
    lines = [
        (
            "[Sun Jan 08 14:51:27 2023] You receive 2 platinum, "
            "3 gold, 3 silver and 4 copper as your split."
        ),
        (
            "[Sun Jan 08 14:54:06 2023] You receive 5 platinum 1 gold "
            "2 silver 3 copper from Ulan Meadowgreen for the Fine Steel Warhammer(s)."
        ),
    ]

    _, _, summary = log_parser.parse_log_lines(lines)

    assert summary.loot_cash_count == 1
    assert summary.merch_cash_count == 1
    assert summary.loot_cash == money_sorter.Cash(2, 3, 3, 4)
    assert summary.merch_cash == money_sorter.Cash(5, 1, 2, 3)


def test_parser_characterizes_zone_after_login_behavior():
    lines = [
        "[Sat Sep 24 19:51:48 2022] Welcome to EverQuest!",
        "[Sun Jan 08 15:01:29 2023] You have entered Lake Rathetear.",
    ]

    _, zone_list, summary = log_parser.parse_log_lines(lines)

    assert summary.zone_count == 1
    assert zone_list.get_raw_eq_list() == ["Lake Rathetear"]


def test_print_summary_only_includes_requested_rollups(capsys):
    kill_list = EQList()
    for name in [
        "froglok",
        "froglok",
        "ghoul",
        "ghoul",
        "ghoul",
        "orc pawn",
        "orc pawn",
        "skeleton",
        "wolf",
        "zombie",
    ]:
        kill_list.add(name)

    zone_list = EQList()
    for name in [
        "Grobb",
        "Grobb",
        "Innothule Swamp",
        "Lake Rathetear",
        "South Karana",
        "Splitpaw Lair",
        "West Freeport",
        "East Freeport",
    ]:
        zone_list.add(name)

    kill_list.sort_lists()
    zone_list.sort_lists()
    summary = log_parser.ParseSummary(
        first_login_message="[Sat Sep 24 19:51:48 2022] Welcome to EverQuest!",
        most_recent_message="[Tue Nov 25 01:28:08 2025] Logging is on.",
        line_count=100,
        login_count=2,
        death_count=3,
        zone_count=8,
        kill_count=10,
        level_count=7,
        level_lost_count=1,
        current_level=59,
        loot_cash_count=4,
        merch_cash_count=5,
        loot_cash=money_sorter.Cash(1, 2, 3, 4),
        merch_cash=money_sorter.Cash(5, 6, 7, 8),
    )

    summary_formatter.print_summary(kill_list, zone_list, summary)

    output = capsys.readouterr().out

    assert "Top 5 killed creatures:" in output
    assert "1. ghoul: 3" in output
    assert "Top 5 visited zones:" in output
    assert "1. Grobb: 2" in output
    assert "First log: [Sat Sep 24 19:51:48 2022] Welcome to EverQuest!" in output
    assert "Most recent message:" not in output
    assert "Total logs: 100" in output
    assert "Logins: 2" in output
    assert "Deaths: 3" in output
    assert "Zone Count: 8" in output
    assert "Kill Count: 10" in output
    assert "Levels Lost: 1" in output
    assert "Level: 59" in output
    assert "Current Level" not in output
    assert "Looted coin: 1p 2g 3s 4c" in output
    assert "Coin from Merchants: 5p 6g 7s 8c" in output
    assert "Level Count" not in output
    assert "Login Count" not in output
    assert "LevelLost Count" not in output
    assert "Loot Cash Count" not in output
    assert "Merch Cash Count" not in output
    assert "6. " not in output
