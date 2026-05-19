import money_sorter

FULL_CASH_LINE = (
    "[Thu Oct 27 21:00:52 2022] You receive 17 platinum, 512 gold, "
    "3 silver, 325 copper"
)


def test_parse_cash_returns_named_cash_value():
    assert money_sorter.parse_cash(FULL_CASH_LINE) == money_sorter.Cash(
        platinum=17,
        gold=512,
        silver=3,
        copper=325,
    )


def test_cash_can_be_added_and_normalized():
    cash = money_sorter.Cash(gold=10, silver=17, copper=17)

    assert cash.normalize() == money_sorter.Cash(platinum=1, gold=1, silver=8, copper=7)


# Combined regex: parse_cash extracts all four denominations in one pass
def test_parse_cash_single_denomination():
    line = "[Wed Oct 26 22:04:16 2022] You receive 7 copper from the corpse."
    assert money_sorter.parse_cash(line) == money_sorter.Cash(copper=7)


def test_parse_cash_no_denomination():
    line = "[Sun Jan 08 15:01:29 2023] You have entered Lake Rathetear."
    assert money_sorter.parse_cash(line) == money_sorter.Cash()


def test_parse_cash_all_four_denominations():
    line = (
        "[Thu Oct 27 21:00:52 2022] You receive 17 platinum, 512 gold, "
        "3 silver and 325 copper from the corpse."
    )
    assert money_sorter.parse_cash(line) == money_sorter.Cash(
        platinum=17, gold=512, silver=3, copper=325
    )
