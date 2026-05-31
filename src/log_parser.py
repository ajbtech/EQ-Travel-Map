"""Streams EverQuest log files and aggregates them into a parsed summary.

Each log line is classified by ``line_reader``; events update a ``ParserState``
which is finalized into an immutable ``ParseSummary`` plus kill / zone tallies.
Files are read lazily so multi-gigabyte archives stay out of memory.
"""

import itertools
import re
from dataclasses import dataclass, field, fields
from datetime import datetime
from pathlib import Path

import line_reader
import money_sorter
from eq_list import EQList

TIMESTAMP_PATTERN = re.compile(r"^\[(?P<timestamp>.+?)\]")
TIMESTAMP_FORMAT = "%a %b %d %H:%M:%S %Y"
LOG_ENCODING = "utf-8"
# A rogue ability can land a one-off ~32k backstab; cap it so the tracked
# backstab max reflects normal hits rather than the spike.
BACKSTAB_DAMAGE_CAP = 10000


@dataclass(frozen=True)
class TimelineEvent:
    kind: line_reader.EventType
    value: object = None


@dataclass
class ParserState:
    kill_list: EQList = field(default_factory=EQList)
    zone_list: EQList = field(default_factory=EQList)
    spell_list: EQList = field(default_factory=EQList)
    max_damage: dict = field(default_factory=dict)
    first_login_message: str = ""
    line_count: int = 0
    login_count: int = 0
    death_count: int = 0
    zone_count: int = 0
    kill_count: int = 0
    level_count: int = 0
    level_lost_count: int = 0
    current_level: int = 1
    loot_cash_count: int = 0
    merch_cash_count: int = 0
    loot_cash: money_sorter.Cash = field(default_factory=money_sorter.Cash)
    merch_cash: money_sorter.Cash = field(default_factory=money_sorter.Cash)
    most_recent_message: str = ""
    previous_line_is_help: bool = False
    previous_line_is_login: bool = False
    timeline: list = field(default_factory=list)
    jboot_click_count: int = 0
    alcohol_count: int = 0
    totally_intoxicated_count: int = 0


@dataclass
class ParseSummary:
    first_login_message: str
    most_recent_message: str
    line_count: int
    login_count: int
    death_count: int
    zone_count: int
    kill_count: int
    level_count: int
    level_lost_count: int
    current_level: int
    loot_cash_count: int
    merch_cash_count: int
    loot_cash: money_sorter.Cash
    merch_cash: money_sorter.Cash
    max_damage: dict = field(default_factory=dict)
    spell_list: EQList = field(default_factory=EQList)
    timeline: list = field(default_factory=list)
    jboot_click_count: int = 0
    alcohol_count: int = 0
    totally_intoxicated_count: int = 0


@dataclass(frozen=True)
class ParseProgress:
    file_path: Path
    line_count: int


PROGRESS_LINE_INTERVAL = 5000
LINE_COUNT_CHUNK_SIZE = 1024 * 1024


def count_lines_in_files(file_paths):
    total = 0
    for file_path in file_paths:
        total += _count_lines_in_file(file_path)
    return total


def _count_lines_in_file(file_path):
    line_count = 0
    last_byte = b""
    with open(file_path, "rb") as f:
        while True:
            chunk = f.read(LINE_COUNT_CHUNK_SIZE)
            if not chunk:
                break
            line_count += chunk.count(b"\n")
            last_byte = chunk[-1:]
    if last_byte and last_byte != b"\n":
        line_count += 1
    return line_count


def find_log_files(log_folder, character_name):
    log_folder = Path(log_folder)
    log_files = log_folder.glob(f"*eqlog_{character_name}_*.txt")
    return sorted(log_files, key=get_first_log_timestamp)


def get_first_log_timestamp(file_path):
    with open(file_path, encoding=LOG_ENCODING, errors="replace") as f:
        for line in f:
            timestamp = get_line_timestamp(line)
            if timestamp is not None:
                return timestamp
    return datetime.max


def get_line_timestamp(line):
    timestamp_match = TIMESTAMP_PATTERN.match(line)
    if timestamp_match is None:
        return None

    timestamp_text = timestamp_match.group("timestamp")
    try:
        return datetime.strptime(timestamp_text, TIMESTAMP_FORMAT)
    except ValueError:
        return None


def build_empty_summary():
    return build_summary(ParserState())


def record_line_metadata(line, event, state):
    state.line_count += 1
    state.most_recent_message = line
    if event.kind == line_reader.EventType.LOGIN and state.first_login_message == "":
        state.first_login_message = line


def record_zone_name(zone_name, state):
    state.zone_count += 1
    state.zone_list.add(zone_name)
    state.timeline.append(TimelineEvent(line_reader.EventType.ZONE, zone_name))


def add_starting_zones(events, state):
    # EQ often records the starting zone near login; capture it before
    # login/help filtering can suppress that zone event.
    for event in events[:4]:
        if event.kind == line_reader.EventType.ZONE:
            record_zone_name(event.value, state)


def should_record_zone(event, state):
    return (
        event.kind == line_reader.EventType.ZONE
        and not state.previous_line_is_help
        and not state.previous_line_is_login
    )


def update_previous_line_flags(event, state):
    state.previous_line_is_help = event.kind == line_reader.EventType.HELP
    state.previous_line_is_login = event.kind == line_reader.EventType.LOGIN


def record_login(_line, _event, state):
    state.login_count += 1
    state.timeline.append(TimelineEvent(line_reader.EventType.LOGIN))


def record_death(_line, _event, state):
    state.death_count += 1
    state.timeline.append(TimelineEvent(line_reader.EventType.DEATH))


def record_kill(line, event, state):
    state.kill_count += 1
    state.kill_list.add(event.value)
    state.timeline.append(TimelineEvent(line_reader.EventType.KILL, event.value))


def record_level_gain(line, event, state):
    state.level_count += 1
    state.current_level = event.value
    state.timeline.append(
        TimelineEvent(line_reader.EventType.LEVEL_GAINED, event.value)
    )


def record_level_loss(line, event, state):
    state.level_lost_count += 1
    state.current_level = event.value
    state.timeline.append(TimelineEvent(line_reader.EventType.LEVEL_LOST, event.value))


def add_loot_cash(_line, event, state):
    state.loot_cash_count += 1
    state.loot_cash = state.loot_cash.add(event.value)
    state.timeline.append(TimelineEvent(line_reader.EventType.LOOT_CASH, event.value))


def add_merchant_cash(_line, event, state):
    state.merch_cash_count += 1
    state.merch_cash = state.merch_cash.add(event.value)
    state.timeline.append(
        TimelineEvent(line_reader.EventType.MERCHANT_CASH, event.value)
    )


def record_player_damage(_line, event, state):
    damage_type, amount = event.value
    if damage_type == "backstab" and amount > BACKSTAB_DAMAGE_CAP:
        return
    if amount > state.max_damage.get(damage_type, 0):
        state.max_damage[damage_type] = amount


def record_spell_cast(_line, event, state):
    state.spell_list.add(event.value)


def record_jboot_click(_line, _event, state):
    state.jboot_click_count += 1


def record_alcohol_consumed(_line, _event, state):
    state.alcohol_count += 1


def record_totally_intoxicated(_line, _event, state):
    state.totally_intoxicated_count += 1


EVENT_HANDLERS = {
    line_reader.EventType.LOGIN: record_login,
    line_reader.EventType.DEATH: record_death,
    line_reader.EventType.KILL: record_kill,
    line_reader.EventType.LEVEL_GAINED: record_level_gain,
    line_reader.EventType.LEVEL_LOST: record_level_loss,
    line_reader.EventType.LOOT_CASH: add_loot_cash,
    line_reader.EventType.MERCHANT_CASH: add_merchant_cash,
    line_reader.EventType.PLAYER_DAMAGE: record_player_damage,
    line_reader.EventType.SPELL_CAST: record_spell_cast,
    line_reader.EventType.JBOOT_CLICK: record_jboot_click,
    line_reader.EventType.ALCOHOL_CONSUMED: record_alcohol_consumed,
    line_reader.EventType.TOTALLY_INTOXICATED: record_totally_intoxicated,
}


def update_event_counts(line, event, state):
    handler = EVENT_HANDLERS.get(event.kind)
    if handler is not None:
        handler(line, event, state)


def process_line_event(line, event, state):
    record_line_metadata(line, event, state)

    if should_record_zone(event, state):
        record_zone_name(event.value, state)

    update_previous_line_flags(event, state)
    update_event_counts(line, event, state)


def process_log_line(line, state):
    event = line_reader.classify_line(line)
    process_line_event(line, event, state)


def notify_progress(progress_callback, log_file, state):
    if progress_callback is not None:
        progress_callback(ParseProgress(Path(log_file), state.line_count))


def should_notify_line_progress(line_count):
    return line_count > 0 and line_count % PROGRESS_LINE_INTERVAL == 0


def normalize_cash_totals(state):
    state.loot_cash = state.loot_cash.normalize()
    state.merch_cash = state.merch_cash.normalize()


def sort_result_lists(state):
    state.kill_list.sort_lists()
    state.zone_list.sort_lists()
    state.spell_list.sort_lists()


# Every ParseSummary field is also a ParserState field, so the summary is a
# projection of the finalized state. Listing the names once here keeps adding a
# tracked metric to a single edit (add the field to both dataclasses) instead of
# also threading it through a hand-written copy.
_SUMMARY_FIELD_NAMES = tuple(f.name for f in fields(ParseSummary))


def build_summary(state):
    values = {name: getattr(state, name) for name in _SUMMARY_FIELD_NAMES}
    # Defensive copies so later parsing (or reuse of the state) can't mutate the
    # returned summary's collections.
    values["max_damage"] = dict(values["max_damage"])
    values["timeline"] = list(values["timeline"])
    return ParseSummary(**values)


def _ingest_lines(lines, state, after_line=None):
    # The first few lines get the starting-zone special case (a zone logged
    # right at login, before login/help filtering can suppress it); the rest
    # stream straight through. ``lines`` may be a list or a file iterator, so a
    # single iterator drives both halves and never re-reads a line.
    line_iter = iter(lines)
    first_lines = list(itertools.islice(line_iter, 4))
    first_events = [line_reader.classify_line(line) for line in first_lines]
    add_starting_zones(first_events, state)
    for line, event in zip(first_lines, first_events):
        process_line_event(line, event, state)
        if after_line is not None:
            after_line()
    for line in line_iter:
        process_log_line(line, state)
        if after_line is not None:
            after_line()


def parse_log_lines(lines):
    state = ParserState()
    _ingest_lines(lines, state)
    _finalize_state(state)
    return state.kill_list, state.zone_list, build_summary(state)


def _finalize_state(state):
    normalize_cash_totals(state)
    sort_result_lists(state)


def process_log_file(log_file, state, progress_callback=None):
    notify_progress(progress_callback, log_file, state)
    with open(log_file, encoding=LOG_ENCODING, errors="replace") as f:

        def after_line():
            if should_notify_line_progress(state.line_count):
                notify_progress(progress_callback, log_file, state)

        _ingest_lines(f, state, after_line)
    notify_progress(progress_callback, log_file, state)


def parse_log_files(log_files, progress_callback=None):
    state = ParserState()
    for log_file in log_files:
        process_log_file(log_file, state, progress_callback)

    if state.line_count == 0:
        return state.kill_list, state.zone_list, build_empty_summary()

    _finalize_state(state)
    return state.kill_list, state.zone_list, build_summary(state)


def parse_character_logs(log_folder, character_name, progress_callback=None):
    log_files = find_log_files(log_folder, character_name)
    return parse_log_files(log_files, progress_callback)
