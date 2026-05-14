import re
from dataclasses import dataclass

COIN_PATTERNS = {
    "platinum": re.compile(r"(\d+)\s?(?=platinum)"),
    "gold": re.compile(r"(\d+)\s?(?=gold)"),
    "silver": re.compile(r"(\d+)\s?(?=silver)"),
    "copper": re.compile(r"(\d+)\s?(?=copper)"),
}


@dataclass(frozen=True)
class Cash:
    platinum: int = 0
    gold: int = 0
    silver: int = 0
    copper: int = 0

    def __iter__(self):
        yield self.platinum
        yield self.gold
        yield self.silver
        yield self.copper

    def add(self, other):
        return Cash(
            platinum=self.platinum + other.platinum,
            gold=self.gold + other.gold,
            silver=self.silver + other.silver,
            copper=self.copper + other.copper,
        )

    def normalize(self):
        total_copper = (
            self.copper + self.silver * 10 + self.gold * 100 + self.platinum * 1000
        )
        platinum, remainder = divmod(total_copper, 1000)
        gold, remainder = divmod(remainder, 100)
        silver, copper = divmod(remainder, 10)
        return Cash(platinum, gold, silver, copper)


def parse_cash(line):
    return Cash(
        platinum=get_coin_value("platinum", line),
        gold=get_coin_value("gold", line),
        silver=get_coin_value("silver", line),
        copper=get_coin_value("copper", line),
    )


def get_coin_value(coin_type, line):
    match = COIN_PATTERNS[coin_type].search(line)
    if match is None:
        return 0
    return int(match.group(1))


def get_plat(line):
    return get_coin_value("platinum", line)


def get_gold(line):
    return get_coin_value("gold", line)


def get_silver(line):
    return get_coin_value("silver", line)


def get_copper(line):
    return get_coin_value("copper", line)


def sort_cash(plat, gold, silver, copper):
    return Cash(plat, gold, silver, copper).normalize()
