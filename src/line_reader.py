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
# Mob loot is capped at 99 cp / sp / pp per corpse; gold can exceed 99.
# A loot-cash line above this on any non-gold denom must be a self-corpse
# retrieval (the player's own dropped purse), not mob loot.
MOB_COIN_CAP = 99
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
PLAYER_DAMAGE_PATTERN = re.compile(
    r"\bYou (\w+) .+ for (\d+) points? of (non-melee )?damage\."
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
    ZONE = "zone"


@dataclass(frozen=True)
class LineEvent:
    kind: EventType = EventType.EMPTY
    value: str | int | None = None


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


def is_line_loot(line):
    return "--You have looted a " in line


# Returns True for looting mob corpses, NOT for selling items or for
# retrieving the player's own corpse (detected via the mob coin cap).
def is_line_loot_cash(line):
    receive = "You receive" in line
    coin = any(coin_type in line for coin_type in COIN_TYPES)
    for_the = "for the" in line
    if not (receive and coin and not for_the):
        return False
    return not _exceeds_mob_coin_cap(line)


def _exceeds_mob_coin_cap(line):
    cash = money_sorter.parse_cash(line)
    return (
        cash.platinum > MOB_COIN_CAP
        or cash.silver > MOB_COIN_CAP
        or cash.copper > MOB_COIN_CAP
    )


# Returns True for selling items, NOT for looting corpses
def is_line_merch_cash(line):
    receive = "You receive" in line
    coin = any(coin_type in line for coin_type in COIN_TYPES)
    for_the = "for the" in line
    return receive and coin and for_the


def is_line_zone(line):
    return ZONE_TEXT in line


def is_line_help(line):
    return HELP_TEXT in line


def is_line_chat(line):
    return CHAT_PATTERN.search(line) is not None


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
        return LineEvent(EventType.MERCHANT_CASH)
    if is_line_loot_cash(line):
        return LineEvent(EventType.LOOT_CASH)
    return EMPTY_LINE_EVENT
