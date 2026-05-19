import money_sorter

FULL_CASH_LINE = (
    "[Thu Oct 27 21:00:52 2022] You receive 17 platinum, 512 gold, "
    "3 silver, 325 copper"
)


def test_plat():
    assert money_sorter.get_plat(FULL_CASH_LINE) == 17


def test_gold():
    assert money_sorter.get_gold(FULL_CASH_LINE) == 512


def test_silver():
    assert money_sorter.get_silver(FULL_CASH_LINE) == 3


def test_copper():
    assert money_sorter.get_copper(FULL_CASH_LINE) == 325


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


def test_null_input():
    line = ""
    assert money_sorter.get_plat(line) == 0
    assert money_sorter.get_gold(line) == 0
    assert money_sorter.get_silver(line) == 0
    assert money_sorter.get_copper(line) == 0


def test_sort_null_input():
    plat = 0
    gold = 0
    silver = 0
    copper = 0
    plat_sorted, gold_sorted, silver_sorted, copper_sorted = money_sorter.sort_cash(
        plat, gold, silver, copper
    )
    assert plat_sorted == 0
    assert gold_sorted == 0
    assert silver_sorted == 0
    assert copper_sorted == 0


def test_input_case_1():
    line = (
        "[Thu Oct 27 21:00:52 2022] You receive 3 gold, 2 silver "
        "and 9 copper from the corpse."
    )
    plat = money_sorter.get_plat(line)
    gold = money_sorter.get_gold(line)
    silver = money_sorter.get_silver(line)
    copper = money_sorter.get_copper(line)
    assert plat == 0
    assert gold == 3
    assert silver == 2
    assert copper == 9


def test_sort_case_1():
    plat = 0
    gold = 3
    silver = 2
    copper = 9
    plat_sorted, gold_sorted, silver_sorted, copper_sorted = money_sorter.sort_cash(
        plat, gold, silver, copper
    )
    assert plat_sorted == 0
    assert gold_sorted == 3
    assert silver_sorted == 2
    assert copper_sorted == 9


def test_input_case_2():
    line = "[Wed Oct 26 22:04:16 2022] You receive 7 copper from the corpse."
    plat = money_sorter.get_plat(line)
    gold = money_sorter.get_gold(line)
    silver = money_sorter.get_silver(line)
    copper = money_sorter.get_copper(line)
    assert plat == 0
    assert gold == 0
    assert silver == 0
    assert copper == 7


def test_sort_case_2():
    plat = 0
    gold = 0
    silver = 0
    copper = 7
    plat_sorted, gold_sorted, silver_sorted, copper_sorted = money_sorter.sort_cash(
        plat, gold, silver, copper
    )
    assert plat_sorted == 0
    assert gold_sorted == 0
    assert silver_sorted == 0
    assert copper_sorted == 7


def test_input_case_3():
    line = (
        "[Mon Oct 24 21:17:09 2022] You receive 29 platinum, "
        "398 gold and 586 silver from the corpse."
    )
    plat = money_sorter.get_plat(line)
    gold = money_sorter.get_gold(line)
    silver = money_sorter.get_silver(line)
    copper = money_sorter.get_copper(line)
    assert plat == 29
    assert gold == 398
    assert silver == 586
    assert copper == 0


def test_sort_case_3():
    plat = 29
    gold = 398
    silver = 586
    copper = 0
    plat_sorted, gold_sorted, silver_sorted, copper_sorted = money_sorter.sort_cash(
        plat, gold, silver, copper
    )
    assert copper_sorted == 0
    assert silver_sorted == 6
    assert gold_sorted == 6
    assert plat_sorted == 74


def test_input_case_4():
    line = (
        "[Tue Nov 22 22:03:48 2022] You receive 10 gold, "
        "17 silver and 17 copper as your split."
    )
    plat = money_sorter.get_plat(line)
    gold = money_sorter.get_gold(line)
    silver = money_sorter.get_silver(line)
    copper = money_sorter.get_copper(line)
    assert plat == 0
    assert gold == 10
    assert silver == 17
    assert copper == 17


def test_sort_case_4():
    plat = 0
    gold = 10
    silver = 17
    copper = 17
    plat_sorted, gold_sorted, silver_sorted, copper_sorted = money_sorter.sort_cash(
        plat, gold, silver, copper
    )
    assert plat_sorted == 1
    assert gold_sorted == 1
    assert silver_sorted == 8
    assert copper_sorted == 7


def test_input_case_5():
    line = (
        "[Sat Dec 10 07:35:12 2022] You receive 16 platinum 7 gold "
        "8 silver 8 copper from Ulan Meadowgreen for the Great Staff(s)."
    )
    plat = money_sorter.get_plat(line)
    gold = money_sorter.get_gold(line)
    silver = money_sorter.get_silver(line)
    copper = money_sorter.get_copper(line)
    assert plat == 16
    assert gold == 7
    assert silver == 8
    assert copper == 8


def test_sort_case_5():
    plat = 16
    gold = 7
    silver = 8
    copper = 8
    plat_sorted, gold_sorted, silver_sorted, copper_sorted = money_sorter.sort_cash(
        plat, gold, silver, copper
    )
    assert plat_sorted == 16
    assert gold_sorted == 7
    assert silver_sorted == 8
    assert copper_sorted == 8


def test_input_case_6():
    line = (
        "[Fri Dec 09 23:34:14 2022] You receive 45 gold, "
        "89 silver and 76 copper as your split."
    )
    plat = money_sorter.get_plat(line)
    gold = money_sorter.get_gold(line)
    silver = money_sorter.get_silver(line)
    copper = money_sorter.get_copper(line)
    assert plat == 0
    assert gold == 45
    assert silver == 89
    assert copper == 76


def test_sort_case_6():
    plat = 0
    gold = 45
    silver = 89
    copper = 76
    plat_sorted, gold_sorted, silver_sorted, copper_sorted = money_sorter.sort_cash(
        plat, gold, silver, copper
    )
    assert plat_sorted == 5
    assert gold_sorted == 4
    assert silver_sorted == 6
    assert copper_sorted == 6


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
