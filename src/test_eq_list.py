from eq_list import EQList


def test_add_null():
    test_eq_list = EQList()
    raw_eq_list_old = test_eq_list.get_raw_eq_list()
    name = ""
    test_eq_list.add(name)
    assert test_eq_list.get_raw_eq_list() == raw_eq_list_old


def test_add_length_increase():
    test_eq_list = EQList()
    raw_eq_list_old = test_eq_list.get_raw_eq_list()
    name = "froglok"
    test_eq_list.add(name)
    raw_eq_list = test_eq_list.get_raw_eq_list()
    assert len(raw_eq_list) == len(raw_eq_list_old) + 1


def test_add_item():
    test_eq_list = EQList()
    name = "froglok"
    test_eq_list.add(name)
    assert test_eq_list.get_raw_eq_list()[-1] == name


def test_sort_type():
    desired_result = ["froglok", "froglok", "ghoul", "greater skeleton"]
    test_eq_list = EQList()
    test_eq_list.add("froglok")
    test_eq_list.add("greater skeleton")
    test_eq_list.add("froglok")
    test_eq_list.add("ghoul")
    test_eq_list.sort_lists()
    type_sorted_eq_list = test_eq_list.get_type_sorted_eq_list()
    assert type_sorted_eq_list == desired_result


def test_sort_type_with_caps():
    desired_result = [
        "froglok",
        "froglok",
        "ghoul",
        "greater skeleton",
        "Vhalen Nostrolo",
    ]
    test_eq_list = EQList()
    test_eq_list.add("froglok")
    test_eq_list.add("greater skeleton")
    test_eq_list.add("Vhalen Nostrolo")
    test_eq_list.add("froglok")
    test_eq_list.add("ghoul")
    test_eq_list.sort_lists()
    type_sorted_eq_list = test_eq_list.get_type_sorted_eq_list()
    assert type_sorted_eq_list == desired_result


def test_sort_alpha_count_with_caps():
    desired_result = [
        ("froglok", 2),
        ("ghoul", 1),
        ("greater skeleton", 1),
        ("Vhalen Nostrolo", 1),
    ]
    test_eq_list = EQList()
    test_eq_list.add("froglok")
    test_eq_list.add("greater skeleton")
    test_eq_list.add("Vhalen Nostrolo")
    test_eq_list.add("froglok")
    test_eq_list.add("ghoul")
    test_eq_list.sort_lists()
    alpha_count_sorted_eq_list = test_eq_list.get_alpha_count_sorted_eq_list()
    assert alpha_count_sorted_eq_list == desired_result


def test_sort_count_alpha_with_caps():
    desired_result = [
        ("ghoul", 3),
        ("froglok", 2),
        ("greater skeleton", 1),
        ("Vhalen Nostrolo", 1),
    ]
    test_eq_list = EQList()
    test_eq_list.add("froglok")
    test_eq_list.add("ghoul")
    test_eq_list.add("greater skeleton")
    test_eq_list.add("Vhalen Nostrolo")
    test_eq_list.add("froglok")
    test_eq_list.add("ghoul")
    test_eq_list.add("ghoul")
    test_eq_list.sort_lists()
    count_alpha_sorted_eq_list = test_eq_list.get_count_alpha_sorted_eq_list()
    assert count_alpha_sorted_eq_list == desired_result
