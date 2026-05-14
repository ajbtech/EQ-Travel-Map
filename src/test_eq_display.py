import pytest

import eq_display


def test_get_zone_center_innothule():
    assert eq_display.get_zone_center("Innothule Swamp") == (1518, 768)


def test_default_map_image_uses_original_zone_map():
    assert eq_display.MAP_IMAGE_PATH.name == "zone_map.png"


def test_existing_zone_center_is_preserved_when_map_label_differs():
    assert eq_display.get_zone_center("Southern Plains of Karana") == (884, 609)


def test_infected_paw_uses_splitpaw_lair_center():
    assert eq_display.get_zone_center("Infected Paw") == (
        eq_display.get_zone_center("Splitpaw Lair")
    )


def test_extracted_zone_centers_are_available():
    assert eq_display.get_zone_center("Surefall Glade") == (586, 392)
    assert eq_display.get_zone_center("Great Divide") == (1108, 1282)
    assert eq_display.get_zone_center("West Cabilis") == (2320, 1112)


def test_log_name_aliases_are_available():
    assert eq_display.get_zone_center("The Overthere") == (2140, 995)
    assert eq_display.get_zone_center("Kael Drakkal") == (1108, 1355)
    assert eq_display.get_zone_center("The Wakening Lands") == (1031, 1361)


def test_shifted_zone_center_uses_smaller_jitter_radius(monkeypatch):
    monkeypatch.setattr(eq_display, "random", lambda: 1)

    shifted_center = eq_display.get_shifted_zone_center("Grobb")

    assert shifted_center == (1538.75, 864.75)


def test_shifted_zone_center_starts_at_exact_center(monkeypatch):
    monkeypatch.setattr(eq_display, "random", lambda: 1)

    shifted_center = eq_display.get_shifted_zone_center("Grobb", visit_number=1)

    assert shifted_center == (1520, 846)


def test_shifted_zone_center_reaches_max_jitter_at_twenty_five_visits(monkeypatch):
    monkeypatch.setattr(eq_display, "random", lambda: 1)

    shifted_center = eq_display.get_shifted_zone_center("Grobb", visit_number=25)

    assert shifted_center == (1538.75, 864.75)


def test_shifted_zone_center_scales_to_total_visits_when_more_than_twenty_five(
    monkeypatch,
):
    monkeypatch.setattr(eq_display, "random", lambda: 1)

    midway_center = eq_display.get_shifted_zone_center(
        "Grobb",
        visit_number=50,
        total_visits=100,
    )
    final_center = eq_display.get_shifted_zone_center(
        "Grobb",
        visit_number=100,
        total_visits=100,
    )

    assert midway_center == pytest.approx((1529.280303, 855.280303))
    assert final_center == (1538.75, 864.75)


def test_make_rainbow_starts_at_red():
    assert eq_display.make_rainbow(0) == (1, 0, 0)


def test_make_rainbow_moves_through_classic_color_stops_then_ends_at_red():
    assert eq_display.make_rainbow(0.1) == pytest.approx((1, 1, 0))
    assert eq_display.make_rainbow(0.3) == pytest.approx((0, 1, 0))
    assert eq_display.make_rainbow(0.5) == pytest.approx((0, 1, 1))
    assert eq_display.make_rainbow(0.7) == pytest.approx((0, 0, 1))
    assert eq_display.make_rainbow(0.9) == pytest.approx((1, 0, 1))
    assert eq_display.make_rainbow(1) == pytest.approx((1, 0, 0))


def test_map_renderer_saves_map_only_by_default(tmp_path):
    output_path = tmp_path / "map_only.png"
    renderer = eq_display.MapRenderer()

    renderer.save_map(output_path)

    image = eq_display.img.imread(output_path)

    assert image.shape[1] == eq_display.MAP_PIXEL_WIDTH


def test_map_renderer_can_extend_canvas_for_metrics_panel(tmp_path):
    output_path = tmp_path / "map_with_metrics.png"
    renderer = eq_display.MapRenderer(include_metrics_panel=True)

    renderer.draw_metrics(["Top 5 killed creatures:", "1. ghoul = 3"])
    renderer.save_map(output_path)

    image = eq_display.img.imread(output_path)

    assert image.shape[1] > eq_display.MAP_PIXEL_WIDTH
    assert image[10, eq_display.MAP_PIXEL_WIDTH + 10, 3] == pytest.approx(1)
