from collections import Counter


class EQList:
    def __init__(self):
        self.raw_eq_list = []
        self.type_sorted_eq_list = []
        self.alpha_count_sorted_eq_list = []
        self.count_alpha_sorted_eq_list = []

    def add(self, name):
        if name != "":
            self.raw_eq_list.append(name)

    def get_raw_eq_list(self):
        return self.raw_eq_list.copy()

    def get_type_sorted_eq_list(self):
        return self.type_sorted_eq_list.copy()

    def get_alpha_count_sorted_eq_list(self):
        return self.alpha_count_sorted_eq_list.copy()

    def get_count_alpha_sorted_eq_list(self):
        return self.count_alpha_sorted_eq_list.copy()

    def _sort_by_type(self, list_in):
        return sorted(list_in, key=str.lower)

    def _sort_by_count(self, list_in):
        return list(Counter(list_in).items())

    def _sort_by_count_alpha(self, list_in):
        return sorted(
            Counter(list_in).items(),
            key=lambda item: (-item[1], item[0].lower()),
        )

    def sort_lists(self):
        self.type_sorted_eq_list = self._sort_by_type(self.raw_eq_list)
        self.alpha_count_sorted_eq_list = self._sort_by_count(self.type_sorted_eq_list)
        self.count_alpha_sorted_eq_list = self._sort_by_count_alpha(self.raw_eq_list)
