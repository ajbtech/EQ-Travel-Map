import log_parser
import money_sorter
import summary_formatter
from eq_list import EQList


def test_build_top_count_lines_limits_results_to_requested_count():
    eq_list = EQList()
    for name in ["a", "a", "b", "b", "b", "c"]:
        eq_list.add(name)
    eq_list.sort_lists()

    lines = summary_formatter.build_top_count_lines("Top", eq_list, limit=2)

    assert lines == ["Top:", "1. b: 3", "2. a: 2"]


def test_build_top_count_lines_adds_commas_to_large_counts():
    eq_list = EQList()
    for _ in range(1000):
        eq_list.add("ghoul")
    eq_list.sort_lists()

    lines = summary_formatter.build_top_count_lines("Top", eq_list, limit=1)

    assert lines == ["Top:", "1. ghoul: 1,000"]


def test_build_summary_lines_formats_cash_and_counts():
    kill_list = EQList()
    zone_list = EQList()
    kill_list.add("ghoul")
    zone_list.add("Grobb")
    kill_list.sort_lists()
    zone_list.sort_lists()
    summary = log_parser.ParseSummary(
        first_login_message="[Sat Sep 24 19:51:48 2022] Welcome to EverQuest!",
        most_recent_message="[Sat Sep 24 19:52:00 2022] Logging is on.",
        line_count=2460366,
        login_count=1471,
        death_count=0,
        zone_count=1990,
        kill_count=8042,
        level_count=0,
        level_lost_count=0,
        current_level=1,
        loot_cash_count=1,
        merch_cash_count=1,
        loot_cash=money_sorter.Cash(41068, 2, 3, 4),
        merch_cash=money_sorter.Cash(25054, 6, 7, 8),
    )

    lines = summary_formatter.build_summary_lines(
        kill_list,
        zone_list,
        summary,
        "Gorrek",
    )

    assert lines == [
        "Character: Gorrek",
        "",
        "Top 5 killed creatures:",
        "1. ghoul: 1",
        "",
        "Top 5 visited zones:",
        "1. Grobb: 1",
        "",
        "First log: [Sat Sep 24 19:51:48 2022] Welcome to EverQuest!",
        "",
        "Total logs: 2,460,366",
        "Logins: 1,471",
        "Deaths: 0",
        "Zone Count: 1,990",
        "Kill Count: 8,042",
        "Levels Lost: 0",
        "Current Level: 1",
        "Looted coin: 41,068p 2g 3s 4c",
        "Coin from Merchants: 25,054p 6g 7s 8c",
    ]


def test_build_summary_sections_groups_by_section():
    kill_list = EQList()
    zone_list = EQList()
    kill_list.add("ghoul")
    zone_list.add("Grobb")
    kill_list.sort_lists()
    zone_list.sort_lists()
    summary = log_parser.ParseSummary(
        first_login_message="[Sat Sep 24 19:51:48 2022] Welcome to EverQuest!",
        most_recent_message="[Sat Sep 24 19:52:00 2022] Logging is on.",
        line_count=2460366,
        login_count=1471,
        death_count=0,
        zone_count=1990,
        kill_count=8042,
        level_count=0,
        level_lost_count=0,
        current_level=1,
        loot_cash_count=1,
        merch_cash_count=1,
        loot_cash=money_sorter.Cash(41068, 2, 3, 4),
        merch_cash=money_sorter.Cash(25054, 6, 7, 8),
    )

    sections = summary_formatter.build_summary_sections(
        kill_list,
        zone_list,
        summary,
        "Gorrek",
    )

    assert sections.character_line == "Character: Gorrek"
    assert sections.top_kills_lines == ["Top 5 killed creatures:", "1. ghoul: 1"]
    assert sections.top_zones_lines == ["Top 5 visited zones:", "1. Grobb: 1"]
    assert sections.stats_lines == [
        "First log: [Sat Sep 24 19:51:48 2022] Welcome to EverQuest!",
        "Total logs: 2,460,366",
        "Logins: 1,471",
        "Deaths: 0",
        "Zone Count: 1,990",
        "Kill Count: 8,042",
        "Levels Lost: 0",
        "Current Level: 1",
        "Looted coin: 41,068p 2g 3s 4c",
        "Coin from Merchants: 25,054p 6g 7s 8c",
    ]


def test_build_summary_sections_omits_character_line_when_no_name():
    kill_list = EQList()
    zone_list = EQList()
    kill_list.add("ghoul")
    zone_list.add("Grobb")
    kill_list.sort_lists()
    zone_list.sort_lists()
    summary = log_parser.build_empty_summary()

    sections = summary_formatter.build_summary_sections(
        kill_list,
        zone_list,
        summary,
    )

    assert sections.character_line == ""
