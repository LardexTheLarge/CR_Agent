"""Stat values must be physically sensible: no zero HP, no zero speed, no impossible timing."""
import math

import pytest

from sim.data import (
    DECK_CARD_IDS, MELEE_RANGE_MILLITILES, SPEED_TIER_MT_PER_TICK, get_path,
)

ARENA_HALF_WIDTH = 9000
EXPECTED_EVO_CYCLES = {"royal_recruits": 1, "goblin_cage": 2}   # Supercell, Aug 2026

# Every unit-like block in the deck: (card_id, path to the block).
UNIT_BLOCKS = [
    ("royal_recruits", "base"), ("little_prince", "base"), ("little_prince", "guardian"),
    ("goblin_cage", "goblin_brawler"), ("flying_machine", "base"), ("zappies", "base"),
    ("royal_hogs", "base"), ("barbarian_barrel", "spawned_unit"),
]
# Blocks that have hit_speed_ticks / first_hit_ticks directly.
TIMED_BLOCKS = [b for b in UNIT_BLOCKS if b != ("little_prince", "base")]


def block(deck, card_id, path):
    return get_path(deck[card_id], path, where=f"{card_id}.json")


def ids(blocks):
    return [f"{c}:{p}" for c, p in blocks]


@pytest.mark.parametrize("card_id,path", UNIT_BLOCKS, ids=ids(UNIT_BLOCKS))
def test_unit_has_positive_hp_damage_speed_and_range(deck, card_id, path):
    b = block(deck, card_id, path)
    assert 0 < b["hitpoints"] <= 10_000
    assert 0 < b["damage"] <= 2_000
    assert b["speed_millitiles_per_tick"] > 0
    assert 0 < b["range_millitiles"] <= 10_000
    assert 200 <= b["collision_radius_millitiles"] <= 2_000


@pytest.mark.parametrize("card_id,path", UNIT_BLOCKS, ids=ids(UNIT_BLOCKS))
def test_unit_mass_is_filled_in(deck, card_id, path):
    mass = block(deck, card_id, path)["mass"]
    assert mass is not None, f"{card_id}.{path}.mass is still null"
    assert 1 <= mass <= 20


@pytest.mark.parametrize("card_id,path", TIMED_BLOCKS, ids=ids(TIMED_BLOCKS))
def test_unit_timing_is_consistent(deck, card_id, path):
    b = block(deck, card_id, path)
    assert 4 <= b["hit_speed_ticks"] <= 200
    assert 1 <= b["first_hit_ticks"] <= b["hit_speed_ticks"]
    if "load_time_ticks" in b:
        assert b["load_time_ticks"] == b["hit_speed_ticks"] - b["first_hit_ticks"]


@pytest.mark.parametrize("card_id,path", UNIT_BLOCKS, ids=ids(UNIT_BLOCKS))
def test_unit_speed_matches_its_tier(deck, card_id, path):
    b = block(deck, card_id, path)
    tier = b["movement_speed_tier"]
    assert tier in SPEED_TIER_MT_PER_TICK
    assert b["speed_millitiles_per_tick"] == SPEED_TIER_MT_PER_TICK[tier]


@pytest.mark.parametrize("card_id,path", UNIT_BLOCKS, ids=ids(UNIT_BLOCKS))
def test_melee_range_matches_its_tier(deck, card_id, path):
    b = block(deck, card_id, path)
    tier = b.get("range_tier")
    if tier is not None:
        assert b["range_millitiles"] == MELEE_RANGE_MILLITILES[tier]


@pytest.mark.parametrize("card_id,path", UNIT_BLOCKS, ids=ids(UNIT_BLOCKS))
def test_sight_range_covers_attack_range(deck, card_id, path):
    b = block(deck, card_id, path)
    if "sight_range_millitiles" in b:
        assert b["sight_range_millitiles"] >= b["range_millitiles"]


@pytest.mark.parametrize("card_id", ["royal_recruits", "little_prince", "flying_machine", "zappies", "royal_hogs"])
def test_troop_block_has_deploy_time_and_count(deck, card_id):
    b = deck[card_id]["base"]
    assert 0 < b["deploy_time_ticks"] <= 60
    assert b["unit_count"] >= 1


@pytest.mark.parametrize("card_id", ["royal_recruits", "zappies", "royal_hogs"])
def test_spawn_offsets_match_unit_count_and_fit_in_the_arena(deck, card_id):
    card = deck[card_id]
    offsets = card["spawn"]["offsets_millitiles"]
    assert len(offsets) == card["base"]["unit_count"]
    points = {(o["x"], o["y"]) for o in offsets}
    assert len(points) == len(offsets), "two units share a spawn point"
    radius = card["base"]["collision_radius_millitiles"]
    assert max(abs(o["x"]) for o in offsets) + radius <= ARENA_HALF_WIDTH


def test_royal_recruits_shield_and_charge(deck):
    card = deck["royal_recruits"]
    assert 0 < card["base"]["shield_hitpoints"] <= 1_000
    assert card["shield"]["hitpoints"] == card["base"]["shield_hitpoints"]
    charge = card["evolution"]["charge"]
    assert charge["distance_millitiles"] == 2500
    assert charge["speed_millitiles_per_tick"] > card["base"]["speed_millitiles_per_tick"]
    assert charge["damage"] == charge["damage_multiplier"] * card["base"]["damage"]


@pytest.mark.parametrize("card_id,cycles", sorted(EXPECTED_EVO_CYCLES.items()))
def test_evolution_cycles_match_the_game(deck, card_id, cycles):
    evo = deck[card_id]["evolution"]
    assert evo["activation"]["cycles_required"] == cycles
    assert evo["elixir"] == deck[card_id]["base"]["elixir"]


def test_little_prince_attack_ramp_speeds_up(deck):
    stages = deck["little_prince"]["attack_ramp"]["stages"]
    ticks = [s["hit_speed_ticks"] for s in stages]
    assert len(ticks) == 3
    assert ticks == sorted(ticks, reverse=True) and len(set(ticks)) == 3
    assert deck["little_prince"]["attack_ramp"]["hit_speed_conservation_ticks"] >= 0


def test_little_prince_ability_is_usable(deck):
    ability = deck["little_prince"]["champion_ability"]
    assert 1 <= ability["elixir_cost"] <= 10
    assert ability["uses_per_match"] >= 1
    assert ability["cast_time_ticks"] >= 1
    guardian = deck["little_prince"]["guardian"]
    assert guardian["charge_damage"] >= guardian["damage"]
    assert ability["dash"]["range_millitiles"] > 0


def test_goblin_cage_building_decays_over_its_lifetime(deck):
    base = deck["goblin_cage"]["base"]
    assert base["hitpoints"] > 0 and base["lifetime_ticks"] > 0
    lifetime_s = base["lifetime_ticks"] / 20
    assert math.isclose(base["hitpoints_lost_per_second"] * lifetime_s, base["hitpoints"], abs_tol=lifetime_s)
    assert base["can_attack"] is False


def test_goblin_cage_evolution_capture_is_defined(deck):
    capture = deck["goblin_cage"]["evolution"]["capture"]
    assert capture["capture_range_millitiles"] > 0
    assert capture["capture_cooldown_ticks"] >= 1
    assert capture["damage_per_hit"] > 0
    assert capture["damage_hit_interval_ticks"] >= 1


def test_royal_hogs_only_attack_buildings(deck):
    b = deck["royal_hogs"]["base"]
    assert set(b["target_types"]) <= {"building", "tower"}
    assert b["attacks_air"] is False
    assert deck["royal_hogs"]["movement"]["can_cross_river"] is True


def test_flying_machine_is_an_air_troop_that_hits_air(deck):
    card = deck["flying_machine"]
    assert card["base"]["is_flying"] is True
    assert "air_troop" in card["base"]["target_types"]
    assert card["movement"]["ignores_river"] is True


def test_zappies_stun_is_positive(deck):
    assert deck["zappies"]["stun"]["duration_ticks"] >= 1


def test_arrows_waves_add_up(deck):
    b = deck["arrows"]["base"]
    assert b["wave_count"] >= 1
    assert b["wave_count"] * b["damage_per_wave"] == b["total_damage"]
    assert 0 < b["crown_tower_total_damage"] < b["total_damage"]
    assert b["wave_count"] * b["crown_tower_damage_per_wave"] == b["crown_tower_total_damage"]
    assert 1_000 <= b["radius_millitiles"] <= 6_000
    assert deck["arrows"]["timing"]["impact_delay_ticks"] >= 0


def test_barbarian_barrel_roll_is_consistent(deck):
    b = deck["barbarian_barrel"]["base"]
    assert b["damage"] > 0 and b["radius_millitiles"] > 0
    assert abs(b["roll_distance_millitiles"] - b["roll_speed_millitiles_per_tick"] * b["roll_duration_ticks"]) \
        <= b["roll_speed_millitiles_per_tick"]
    assert deck["barbarian_barrel"]["spawned_unit"]["spawn_trigger"] == "end_of_roll"