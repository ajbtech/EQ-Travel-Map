from collections import Counter


class EQList:
    """Accumulates names (kills, zones, spells) and ranks them by frequency.

    ``add`` collects raw names in arrival order; ``sort_lists`` builds the
    count-then-alphabetical ranking that the summaries display.
    """

    def __init__(self):
        self.raw_eq_list = []
        self.count_alpha_sorted_eq_list = []

    def add(self, name):
        if name != "":
            self.raw_eq_list.append(name)

    def get_raw_eq_list(self):
        return self.raw_eq_list.copy()

    def get_count_alpha_sorted_eq_list(self):
        return self.count_alpha_sorted_eq_list.copy()

    def sort_lists(self):
        self.count_alpha_sorted_eq_list = sorted(
            Counter(self.raw_eq_list).items(),
            key=lambda item: (-item[1], item[0].lower()),
        )
