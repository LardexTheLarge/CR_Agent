"""Tower and arena numbers must be usable and consistent with each other."""
import pytest


def test_arena_bounds_are_18_by_32_tiles(arena):
    b = arena["bounds"]
    assert b["x_max_millitiles"] - b["x_min_millitiles"] == 18_000
    assert b["y_max_millitiles"] - b["y_min_millitiles"] == 32_000


def test_river_and_bridges_line_up(arena):
    river = arena["river"]
    assert river["y_max_millitiles"] - river["y_min_millitiles"] == river["height_millitiles"] > 0
    for bridge in arena["bridges"]:
        assert bridge["y_min_millitiles"] == river["y_min_millitiles"]
        assert bridge["y_max_millitiles"] == river["y_max_millitiles"]
        assert bridge["x_max_millitiles"] - bridge["x_min_millitiles"] == bridge["width_millitiles"] > 0


@pytest.mark.parametrize("side", ["friendly", "enemy"])
def test_towers_sit_inside_the_arena(arena, side):
    b = arena["bounds"]
    sizes = arena["towers"]["footprints_millitiles"]
    for name, pos in arena["towers"][side].items():
        size = sizes["king" if name == "king" else "princess"]
        half_w, half_h = size["width"] // 2, size["height"] // 2
        assert b["x_min_millitiles"] <= pos["x_millitiles"] - half_w
        assert pos["x_millitiles"] + half_w <= b["x_max_millitiles"]
        assert b["y_min_millitiles"] <= pos["y_millitiles"] - half_h
        assert pos["y_millitiles"] + half_h <= b["y_max_millitiles"]


def test_deploy_zone_stops_at_the_river(arena):
    zone = arena["deployment"]["friendly_base_zone"]
    assert zone["y_max_millitiles"] == arena["river"]["y_min_millitiles"]
    assert zone["y_min_millitiles"] == arena["bounds"]["y_min_millitiles"]


@pytest.mark.parametrize("tower_id", ["king_tower", "princess_tower"])
def test_tower_has_positive_stats(towers, tower_id):
    base = towers[tower_id]["base"]
    assert base["hitpoints"] > 0 and base["damage"] > 0
    assert base["hit_speed_ticks"] > 0
    assert base["range_millitiles"] > 0
    assert base["footprint_millitiles"]["width"] == 2 * base["collision_radius_millitiles"]
    assert towers[tower_id]["projectile"]["speed_millitiles_per_tick"] > 0


def test_king_is_tougher_than_princess_and_shoots_slower(towers):
    king, princess = towers["king_tower"]["base"], towers["princess_tower"]["base"]
    assert king["hitpoints"] > princess["hitpoints"]
    assert king["hit_speed_ticks"] >= princess["hit_speed_ticks"]


def test_king_first_shot_delay_matches_arena(towers, arena):
    shot = towers["king_tower"]["activation"]["first_shot"]
    assert shot["aim_ticks"] + shot["pre_fire_ticks"] == shot["total_ticks_from_activation_to_fire"]
    assert arena["towers"]["king_activation"]["wake_up_delay_ticks"] == shot["total_ticks_from_activation_to_fire"]


def test_pocket_is_nine_by_four_tiles(arena):
    zones = arena["deployment"]["pocket_zones"]["geometry_millitiles"]
    for side in zones.values():
        for z in side.values():
            assert z["x_max"] - z["x_min"] == 9_000
            assert z["y_max"] - z["y_min"] == 4_000


def test_elixir_model_is_exact(arena):
    m = arena["match_rules"]
    model = m["elixir_model"]
    assert model["cap_subunits"] == model["subunits_per_elixir"] * m["elixir_cap"]
    assert model["starting_subunits"] == model["subunits_per_elixir"] * m["starting_elixir"]
    assert m["elixir_schedule"][-1]["to_tick"] == m["total_ticks"]