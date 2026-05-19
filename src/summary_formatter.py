from dataclasses import dataclass, field


@dataclass
class SummarySections:
    character_line: str = ""
    top_kills_lines: list = field(default_factory=list)
    top_zones_lines: list = field(default_factory=list)
    stats_lines: list = field(default_factory=list)
    extended_kills_lines: list = field(default_factory=list)
    extended_zones_lines: list = field(default_factory=list)
    extended_spells_lines: list = field(default_factory=list)
    max_damage_lines: list = field(default_factory=list)


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
    extended_kills_lines = build_top_count_lines(
        "Top 25 killed creatures", kill_list, limit=25
    )
    extended_zones_lines = build_top_count_lines(
        "Top 25 visited zones", zone_list, limit=25
    )
    extended_spells_lines = build_top_count_lines(
        "Top 25 cast spells", summary.spell_list, limit=25
    )
    max_damage_lines = build_max_damage_lines(summary.max_damage)
    return SummarySections(
        character_line=character_line,
        top_kills_lines=top_kills_lines,
        top_zones_lines=top_zones_lines,
        stats_lines=stats_lines,
        extended_kills_lines=extended_kills_lines,
        extended_zones_lines=extended_zones_lines,
        extended_spells_lines=extended_spells_lines,
        max_damage_lines=max_damage_lines,
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


_DAMAGE_TYPE_ORDER = ["slash", "pierce", "backstab", "bash", "spell", "crit"]


def build_max_damage_lines(max_damage):
    lines = ["Max hit by damage type:"]
    if not max_damage:
        lines.append("(no data)")
        return lines
    known = [(t, max_damage[t]) for t in _DAMAGE_TYPE_ORDER if t in max_damage]
    extra = sorted((t, v) for t, v in max_damage.items() if t not in _DAMAGE_TYPE_ORDER)
    for damage_type, amount in known + extra:
        lines.append(f"{damage_type}: {format_number(amount)}")
    return lines


def format_number(value):
    return f"{value:,}"


def format_cash(cash):
    return (
        f"{format_number(cash.platinum)}p "
        f"{format_number(cash.gold)}g "
        f"{format_number(cash.silver)}s "
        f"{format_number(cash.copper)}c"
    )


def print_summary(kill_list, zone_list, summary, character_name=None):
    print(
        *build_summary_lines(kill_list, zone_list, summary, character_name),
        sep="\n",
    )
