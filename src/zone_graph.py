import json
import sys
from functools import lru_cache
from pathlib import Path


def _data_root():
    if hasattr(sys, "_MEIPASS"):
        return Path(sys._MEIPASS)
    return Path(__file__).resolve().parents[1]


ZONE_GRAPH_PATH = _data_root() / "zone_graph.json"


@lru_cache(maxsize=1)
def load_zone_graph():
    with open(ZONE_GRAPH_PATH, encoding="utf-8") as f:
        return json.load(f)


def get_canonical_zone_name(zone_name):
    graph = load_zone_graph()
    return graph["aliases"].get(zone_name, zone_name)


@lru_cache(maxsize=1)
def get_adjacent_zone_pairs():
    graph = load_zone_graph()
    return {frozenset((edge["from"], edge["to"])) for edge in graph["edges"]}


def are_adjacent(source_zone, target_zone):
    source_zone = get_canonical_zone_name(source_zone)
    target_zone = get_canonical_zone_name(target_zone)

    if source_zone == target_zone:
        return False

    return frozenset((source_zone, target_zone)) in get_adjacent_zone_pairs()


def is_same_zone(source_zone, target_zone):
    return get_canonical_zone_name(source_zone) == get_canonical_zone_name(target_zone)


@lru_cache(maxsize=1)
def get_zone_centers():
    graph = load_zone_graph()
    centers = {
        name: tuple(data["center"])
        for name, data in graph["nodes"].items()
        if "center" in data
    }
    for alias, target in graph["aliases"].items():
        if target in centers:
            centers[alias] = centers[target]
    return centers


def has_zone_center(name):
    return name in get_zone_centers()


def get_zone_center(name):
    return get_zone_centers()[name]
