"""Classifies a single EverQuest log line into a ``LineEvent``.

This module is the parser's pattern-matching layer: each ``classify_line`` call
returns one event (zone, kill, death, level change, login, loot/merchant cash,
or empty) so ``log_parser`` can stay event-driven and free of regex details.
"""

import re
from dataclasses import dataclass
from enum import Enum

import money_sorter

COIN_TYPES = ("platinum", "gold", "silver", "copper")
# Mob loot never produces more than ~200 of any single denomination per
# corpse; a loot-cash line above this on any denom is the player's own
# dropped purse, not mob loot. Applied to raw per-denom counts before
# normalization to platinum.
MOB_COIN_CAP = 200
# Matches chat verbs (says/say/shouts/shout/auctions/auction/tells/tell/told)
# followed by an optional target phrase, then the comma + opening quote that
# always precedes spoken text in EQ logs.
CHAT_PATTERN = re.compile(r" (?:says?|shouts?|auctions?|tells?|told)\b[^']*?,\s*'")
DEATH_TEXT = "You have been slain by "
HELP_TEXT = "If you need help, click on the EQ Menu "
KILL_TEXT = "You have slain "
LEVEL_GAINED_TEXT = "You have gained a level! Welcome to level "
LEVEL_LOST_TEXT = "You LOST a level! You are now level "
LOGIN_TEXT = "Welcome to EverQuest!"
ZONE_TEXT = "You have entered "
# Cheap substring prefilters so the player-damage / spell-cast regexes
# only run on candidate lines, not every line of a multi-GB log.
PLAYER_DAMAGE_TEXT = " damage."
SPELL_CAST_TEXT = "You begin casting "
PLAYER_DAMAGE_PATTERN = re.compile(
    r"\bYou (?!have\b)(\w+) .+ for (\d+) points? of (non-melee )?damage\."
)
SPELL_CAST_PATTERN = re.compile(r"\bYou begin casting (.+)\.")


class EventType(Enum):
    EMPTY = "empty"
    DEATH = "death"
    HELP = "help"
    KILL = "kill"
    LEVEL_GAINED = "level_gained"
    LEVEL_LOST = "level_lost"
    LOGIN = "login"
    LOOT_CASH = "loot_cash"
    MERCHANT_CASH = "merchant_cash"
    PLAYER_DAMAGE = "player_damage"
    SPELL_CAST = "spell_cast"
    ZONE = "zone"


@dataclass(frozen=True)
class LineEvent:
    kind: EventType = EventType.EMPTY
    value: str | int | tuple | None = None


EMPTY_LINE_EVENT = LineEvent()


def is_line_death(line):
    return DEATH_TEXT in line


def is_line_login(line):
    return LOGIN_TEXT in line


def is_line_kill(line):
    return KILL_TEXT in line


def is_line_level(line):
    return LEVEL_GAINED_TEXT in line


def is_line_level_lost(line):
    return LEVEL_LOST_TEXT in line


def _is_cash_receive_line(line):
    return "You receive" in line and any(coin_type in line for coin_type in COIN_TYPES)


# Returns True for looting mob corpses, NOT for selling items or for
# retrieving the player's own corpse (detected via the mob coin cap).
def _try_classify_loot_cash(line):
    """Return parsed Cash if this is a valid mob-loot cash line, else None."""
    if not (
        "You receive" in line
        and any(ct in line for ct in COIN_TYPES)
        and "for the" not in line
    ):
        return None
    cash = money_sorter.parse_cash(line)
    return None if any(amount > MOB_COIN_CAP for amount in cash) else cash


def is_line_loot_cash(line):
    return _try_classify_loot_cash(line) is not None


# Returns True for selling items, NOT for looting corpses
def is_line_merch_cash(line):
    return _is_cash_receive_line(line) and "for the" in line


def is_line_zone(line):
    return ZONE_TEXT in line


def is_line_help(line):
    return HELP_TEXT in line


def is_line_player_damage(line):
    return PLAYER_DAMAGE_TEXT in line


def is_line_spell_cast(line):
    return SPELL_CAST_TEXT in line


def is_line_chat(line):
    return ", '" in line and CHAT_PATTERN.search(line) is not None


def _clean_up_article(name):
    if name[:2] == "a ":
        name = name[2:]
    if name[:3] == "an ":
        name = name[3:]
    return name


def _get_text_between(line, start_text, end_text):
    start_index = line.find(start_text)
    if start_index == -1:
        return ""

    start_index += len(start_text)
    end_index = line.find(end_text, start_index)
    if end_index == -1:
        return line[start_index:].strip()

    return line[start_index:end_index]


def get_name(line):
    name = _get_text_between(line, DEATH_TEXT, "!")
    if name == "":
        name = _get_text_between(line, KILL_TEXT, "!")
    name = _clean_up_article(name)
    return name


def get_zone(line):
    # Zone names are matched literally against zone_graph.json (with aliases
    # for log-specific phrasings), so leading articles must be preserved -
    # "an Arena (PvP) area" is its own zone phrase, not "The Arena".
    return _get_text_between(line, ZONE_TEXT, ".")


def get_level(line):
    if is_line_level(line):
        level_text = _get_text_between(line, LEVEL_GAINED_TEXT, "!")
    elif is_line_level_lost(line):
        level_text = _get_text_between(line, LEVEL_LOST_TEXT, "!")
    else:
        return None

    return int(level_text)


def get_player_damage(line):
    m = PLAYER_DAMAGE_PATTERN.search(line)
    if m is None:
        return None
    verb = m.group(1)
    amount = int(m.group(2))
    if m.group(3) is not None:
        return "spell", amount
    if verb == "critically":
        return "crit", amount
    return verb, amount


def get_spell_cast(line):
    m = SPELL_CAST_PATTERN.search(line)
    if m is None:
        return None
    return m.group(1)


def classify_line(line):
    if is_line_chat(line):
        return EMPTY_LINE_EVENT
    if is_line_login(line):
        return LineEvent(EventType.LOGIN)
    if is_line_help(line):
        return LineEvent(EventType.HELP)
    if is_line_zone(line):
        return LineEvent(EventType.ZONE, get_zone(line))
    if is_line_death(line):
        return LineEvent(EventType.DEATH)
    if is_line_kill(line):
        return LineEvent(EventType.KILL, get_name(line))
    if is_line_level(line):
        return LineEvent(EventType.LEVEL_GAINED, get_level(line))
    if is_line_level_lost(line):
        return LineEvent(EventType.LEVEL_LOST, get_level(line))
    if is_line_merch_cash(line):
        return LineEvent(EventType.MERCHANT_CASH, money_sorter.parse_cash(line))
    cash = _try_classify_loot_cash(line)
    if cash is not None:
        return LineEvent(EventType.LOOT_CASH, cash)
    if is_line_spell_cast(line):
        spell = get_spell_cast(line)
        if spell is not None:
            return LineEvent(EventType.SPELL_CAST, spell)
    if is_line_player_damage(line):
        damage = get_player_damage(line)
        if damage is not None:
            return LineEvent(EventType.PLAYER_DAMAGE, damage)
    return EMPTY_LINE_EVENT
