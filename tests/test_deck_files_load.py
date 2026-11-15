"""A missing, misnamed or malformed data file must fail loudly before the sim starts."""
import pytest

from sim.data import (
    ARENA_ID, DECK_CARD_IDS, TICK_MS, TILE_MILLITILES, TOWER_IDS,
    DataError, all_data_names, find_data_file, load_data_file,
)

EXPECTED_ELIXIR = {
    "royal_recruits": 7, "little_prince": 3, "goblin_cage": 4, "flying_machine": 4,
    "zappies": 4, "royal_hogs": 5, "arrows": 3, "barbarian_barrel": 2,
}


def test_deck_has_eight_unique_cards():
    assert len(DECK_CARD_IDS) == 8
    assert len(set(DECK_CARD_IDS)) == 8
    assert set(DECK_CARD_IDS) == set(EXPECTED_ELIXIR)


@pytest.mark.parametrize("name", all_data_names())
def test_every_data_file_is_found_exactly_once(name):
    assert find_data_file(name).name == f"{name}.json"


@pytest.mark.parametrize("name", all_data_names())
def test_every_data_file_has_the_shared_header(name):
    data = load_data_file(name)
    assert isinstance(data["schema_version"], int) and data["schema_version"] >= 1
    units = data["meta"]["units"]
    assert units["tick_ms"] == TICK_MS
    assert units["tile_millitiles"] == TILE_MILLITILES
    assert units["integer_only"] is True
    assert data["meta"]["game_version"]
    if name != ARENA_ID:
        assert data["meta"]["card_level"] == 11


@pytest.mark.parametrize("card_id", DECK_CARD_IDS)
def test_card_has_name_and_base_block(deck, card_id):
    card = deck[card_id]
    assert card["card_id"] and isinstance(card["card_id"], str)
    assert card["name"] and isinstance(card["name"], str)
    assert isinstance(card["base"], dict) and card["base"]


@pytest.mark.parametrize("card_id", DECK_CARD_IDS)
def test_card_elixir_cost_is_correct(deck, card_id):
    assert deck[card_id]["base"]["elixir"] == EXPECTED_ELIXIR[card_id]


def test_deck_average_elixir_is_four(deck):
    total = sum(deck[c]["base"]["elixir"] for c in DECK_CARD_IDS)
    assert total / len(DECK_CARD_IDS) == 4.0


def test_missing_file_raises_a_clear_error():
    with pytest.raises(DataError, match="not found"):
        find_data_file("no_such_card")