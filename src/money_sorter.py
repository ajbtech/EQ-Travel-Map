import re
from dataclasses import dataclass

COIN_COMBINED_PATTERN = re.compile(r"(\d+)\s?(platinum|gold|silver|copper)")


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
    values = {m.group(2): int(m.group(1)) for m in COIN_COMBINED_PATTERN.finditer(line)}
    return Cash(
        platinum=values.get("platinum", 0),
        gold=values.get("gold", 0),
        silver=values.get("silver", 0),
        copper=values.get("copper", 0),
    )


def get_coin_value(coin_type, line):
    return getattr(parse_cash(line), coin_type)


