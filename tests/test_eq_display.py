import pytest
from PIL import Image

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
    assert eq_display.get_zone_center("West Cabilis") == (2311, 1106)


def test_log_name_aliases_are_available():
    assert eq_display.get_zone_center("The Overthere") == (2140, 995)
    assert eq_display.get_zone_center("Kael Drakkal") == (1108, 1355)
    assert eq_display.get_zone_center("The Wakening Lands") == (1031, 1361)


def test_max_ring_radius_matches_legacy_jitter_radius():
    assert eq_display.MAX_RING_RADIUS == 18.75


def test_draw_disc_fills_center_with_expected_color():
    renderer = eq_display.MapRenderer()
    x, y = eq_display.MAP_PIXEL_WIDTH // 2, eq_display.MAP_PIXEL_HEIGHT // 2

    renderer.draw_disc((x, y), 10, 0.0)

    expected = eq_display._to_rgba(eq_display.make_rainbow(0.0))
    assert renderer.get_image().getpixel((x, y)) == expected


def test_draw_disc_fills_out_to_its_radius():
    renderer = eq_display.MapRenderer()
    x, y = eq_display.MAP_PIXEL_WIDTH // 2, eq_display.MAP_PIXEL_HEIGHT // 2
    radius = 10

    renderer.draw_disc((x, y), radius, 0.5)

    expected = eq_display._to_rgba(eq_display.make_rainbow(0.5))
    edge_pixel = renderer.get_image().getpixel((x, y - radius + 1))
    assert edge_pixel == expected


def test_make_rainbow_starts_at_red():
    assert eq_display.make_rainbow(0) == (1, 0, 0)


def test_make_rainbow_moves_through_classic_color_stops_then_ends_at_red():
    assert eq_display.make_rainbow(0.1) == pytest.approx((1, 1, 0))
    assert eq_display.make_rainbow(0.3) == pytest.approx((0, 1, 0))
    assert eq_display.make_rainbow(0.5) == pytest.approx((0, 1, 1))
    assert eq_display.make_rainbow(0.7) == pytest.approx((0, 0, 1))
    assert eq_display.make_rainbow(0.9) == pytest.approx((1, 0, 1))
    assert eq_display.make_rainbow(1) == pytest.approx((1, 0, 0))


def test_map_renderer_saves_map_at_expected_dimensions(tmp_path):
    output_path = tmp_path / "map_only.png"
    renderer = eq_display.MapRenderer()

    renderer.save_map(output_path)

    with Image.open(output_path) as image:
        assert image.size == (eq_display.MAP_PIXEL_WIDTH, eq_display.MAP_PIXEL_HEIGHT)


def test_draw_location_circle_paints_ring_pixel_with_expected_color():
    renderer = eq_display.MapRenderer()
    x, y = eq_display.MAP_PIXEL_WIDTH // 2, eq_display.MAP_PIXEL_HEIGHT // 2
    percent = 0.0  # red

    renderer.draw_location_circle((x, y), percent)
    img = renderer.get_image()
    r = eq_display.LOCATION_CIRCLE_RADIUS
    top_pixel = img.getpixel((x, y - r))

    expected = eq_display._to_rgba(eq_display.make_rainbow(percent))
    assert top_pixel == expected


def test_draw_location_circle_center_is_unfilled():
    renderer = eq_display.MapRenderer()
    x, y = eq_display.MAP_PIXEL_WIDTH // 2, eq_display.MAP_PIXEL_HEIGHT // 2

    before = eq_display.MapRenderer().get_image().getpixel((x, y))
    renderer.draw_location_circle((x, y), 0.0)
    after = renderer.get_image().getpixel((x, y))

    assert after == before


def test_for_overlay_draws_on_provided_image_without_base_map():
    from PIL import Image

    w, h = eq_display.MAP_PIXEL_WIDTH, eq_display.MAP_PIXEL_HEIGHT
    canvas = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    renderer = eq_display.MapRenderer.for_overlay(canvas)
    x, y = w // 2, h // 2
    renderer.draw_dot((x, y), 0.0)

    assert canvas.getpixel((x, y)) == eq_display._to_rgba(eq_display.make_rainbow(0.0))


def test_for_overlay_does_not_paste_base_map():
    from PIL import Image

    w, h = eq_display.MAP_PIXEL_WIDTH, eq_display.MAP_PIXEL_HEIGHT
    canvas = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    eq_display.MapRenderer.for_overlay(canvas)

    # All pixels should still be transparent — no map was pasted.
    assert canvas.getpixel((0, 0)) == (0, 0, 0, 0)
