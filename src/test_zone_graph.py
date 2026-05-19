import json
from pathlib import Path

import eq_display

ZONE_GRAPH_PATH = Path(__file__).resolve().parents[1] / "zone_graph.json"


def load_zone_graph():
    with open(ZONE_GRAPH_PATH, encoding="utf-8") as f:
        return json.load(f)


def test_zone_graph_edges_reference_existing_nodes():
    graph = load_zone_graph()
    node_names = set(graph["nodes"])

    missing_nodes = {
        zone_name
        for edge in graph["edges"]
        for zone_name in (edge["from"], edge["to"])
        if zone_name not in node_names
    }

    assert missing_nodes == set()


def test_zone_graph_aliases_reference_existing_nodes():
    graph = load_zone_graph()
    node_names = set(graph["nodes"])

    missing_alias_targets = {
        target for target in graph["aliases"].values() if target not in node_names
    }

    assert missing_alias_targets == set()


def test_zone_graph_nodes_are_available_to_display():
    graph = load_zone_graph()

    missing_display_centers = {
        zone_name
        for zone_name in graph["nodes"]
        if not eq_display.has_zone_center(zone_name)
    }

    assert missing_display_centers == set()


def test_zone_graph_has_no_duplicate_undirected_edges():
    graph = load_zone_graph()
    undirected_edges = [
        tuple(sorted([edge["from"], edge["to"]])) for edge in graph["edges"]
    ]

    assert len(undirected_edges) == len(set(undirected_edges))


def test_zone_graph_includes_boat_connection_between_north_ro_and_iceclad():
    graph = load_zone_graph()
    edges = {frozenset((edge["from"], edge["to"])) for edge in graph["edges"]}

    assert frozenset(("Northern Desert of Ro", "Iceclad Ocean")) in edges


def test_zone_graph_includes_plane_of_sky_connection_to_east_freeport():
    graph = load_zone_graph()
    edges = {frozenset((edge["from"], edge["to"])) for edge in graph["edges"]}

    assert frozenset(("Plane of Sky", "East Freeport")) in edges


def test_zone_graph_aliases_an_arena_pvp_area_to_the_arena():
    # EQ logs write "You have entered an Arena (PvP) area." verbatim; the
    # alias resolves that literal phrase to the canonical "The Arena" node
    # without relying on article stripping.
    graph = load_zone_graph()

    assert graph["aliases"].get("an Arena (PvP) area") == "The Arena"


def test_zone_graph_aliases_log_name_without_apostrophe_for_sirens_grotto():
    # EQ logs write "You have entered Sirens Grotto." with no apostrophe,
    # but the graph node uses the canonical "Siren's Grotto" spelling.
    graph = load_zone_graph()

    assert graph["aliases"].get("Sirens Grotto") == "Siren's Grotto"


def test_zone_graph_aliases_high_keep_to_highpass_keep():
    # EQ logs write "You have entered High Keep." (zone: highkeep), but the
    # map node uses "Highpass Keep" to distinguish it from Highpass Hold.
    graph = load_zone_graph()

    assert graph["aliases"].get("High Keep") == "Highpass Keep"


def test_zone_graph_aliases_qeynos_aqueduct_system_to_qeynos_catacombs():
    # EQ logs write "You have entered The Qeynos Aqueduct System." (zone: qcat),
    # but the map node uses the colloquial name "Qeynos Catacombs".
    graph = load_zone_graph()

    assert graph["aliases"].get("The Qeynos Aqueduct System") == "Qeynos Catacombs"


def test_zone_graph_aliases_northern_felwithe_to_north_felwithe():
    # EQ logs write "You have entered Northern Felwithe." (zone: felwithea),
    # but the map node uses the abbreviated "North Felwithe".
    graph = load_zone_graph()

    assert graph["aliases"].get("Northern Felwithe") == "North Felwithe"


def test_zone_graph_aliases_southern_felwithe_to_south_felwithe():
    # EQ logs write "You have entered Southern Felwithe." (zone: felwitheb),
    # but the map node uses the abbreviated "South Felwithe".
    graph = load_zone_graph()

    assert graph["aliases"].get("Southern Felwithe") == "South Felwithe"


def test_zone_graph_aliases_temple_of_solusek_ro_to_temple_of_sol_ro():
    # EQ logs write "You have entered The Temple of Solusek Ro." (zone: soltemple),
    # but the map node uses the abbreviated "Temple of Sol. Ro".
    graph = load_zone_graph()

    assert graph["aliases"].get("The Temple of Solusek Ro") == "Temple of Sol. Ro"


def test_zone_graph_includes_boat_connections_from_map_dotted_lines():
    graph = load_zone_graph()
    edges = {frozenset((edge["from"], edge["to"])) for edge in graph["edges"]}

    expected_edges = {
        frozenset(("Erud's Crossing", "Erudin Docks")),
        frozenset(("Erud's Crossing", "Erudin")),
        frozenset(("South Qeynos", "Erud's Crossing")),
        frozenset(("Oasis of Marr", "Timorous Deep")),
        frozenset(("Timorous Deep", "Firiona Vie")),
        frozenset(("Timorous Deep", "Overthere")),
        frozenset(("Ocean of Tears", "Butcherblock Mountains")),
        frozenset(("Butcherblock Mountains", "Timorous Deep")),
    }

    assert expected_edges <= edges
