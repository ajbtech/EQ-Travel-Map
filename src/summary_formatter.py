from dataclasses import dataclass, field


@dataclass
class SummarySections:
    character_line: str = ""
    top_kills_lines: list = field(default_factory=list)
    top_zones_lines: list = field(default_factory=list)
    stats_lines: list = field(default_factory=list)


def build_summary_sections(kill_list, zone_list, summary, character_name=None):
    character_line = (
        f"Character: {character_name}" if character_name is not None else ""
    )
    top_kills_lines = build_top_count_lines("Top 5 killed creatures", kill_list)
    top_zones_lines = build_top_count_lines("Top 5 visited zones", zone_list)
    stats_lines = [
        f"First log: {summary.first_login_message.rstrip()}",
        f"Total logs: {format_number(summary.line_count)}",
        f"Logins: {format_number(summary.login_count)}",
        f"Deaths: {format_number(summary.death_count)}",
        f"Zone Count: {format_number(summary.zone_count)}",
        f"Kill Count: {format_number(summary.kill_count)}",
        f"Levels Lost: {format_number(summary.level_lost_count)}",
        f"Current Level: {format_number(summary.current_level)}",
        f"Looted coin: {format_cash(summary.loot_cash)}",
        f"Coin from Merchants: {format_cash(summary.merch_cash)}",
    ]
    return SummarySections(
        character_line=character_line,
        top_kills_lines=top_kills_lines,
        top_zones_lines=top_zones_lines,
        stats_lines=stats_lines,
    )


def build_summary_lines(kill_list, zone_list, summary, character_name=None):
    sections = build_summary_sections(kill_list, zone_list, summary, character_name)
    lines = []
    if sections.character_line:
        lines += [sections.character_line, ""]
    lines += sections.top_kills_lines
    lines += [""]
    lines += sections.top_zones_lines
    lines += ["", sections.stats_lines[0], ""]
    lines += sections.stats_lines[1:]
    return lines


def build_top_count_lines(title, eq_list, limit=5):
    lines = [f"{title}:"]
    for rank, item in enumerate(eq_list.get_count_alpha_sorted_eq_list()[:limit], 1):
        name, count = item
        lines.append(f"{rank}. {name}: {format_number(count)}")
    return lines


def format_number(value):
    return f"{value:,}"


def format_cash(cash):
    plat, gold, silver, copper = cash
    return (
        f"{format_number(plat)}p "
        f"{format_number(gold)}g "
        f"{format_number(silver)}s "
        f"{format_number(copper)}c"
    )


def print_summary(kill_list, zone_list, summary, character_name=None):
    print(
        *build_summary_lines(kill_list, zone_list, summary, character_name),
        sep="\n",
    )
