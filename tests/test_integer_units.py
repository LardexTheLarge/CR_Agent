"""Floats creeping into tick or millitile fields make the sim non-deterministic."""
import re

import pytest

from sim.data import TICKS_PER_SECOND, TILE_MILLITILES, all_data_names, load_data_file, walk

INT_SUFFIX = re.compile(
    r"(_ticks|_millitiles|_millitiles_per_tick|_per_tick|_per_mille|_per_second|_per_20_ticks"
    r"|_subunits|_hitpoints|_damage)$"
)
INT_NAMES = {
    "hitpoints", "damage", "elixir", "mass", "unit_count", "count_per_side", "wave_count",
    "cycles_required", "damage_per_wave", "damage_per_hit", "damage_multiplier", "damage_base",
    "from_tick", "to_tick", "multiplier", "in_game_value", "uses_per_match",
}
FLOAT_OK = re.compile(r"(_s|_tiles|_percent)$|^tiles_per_sec$")


def is_unit_path(path: str, key: str) -> bool:
    """True when the value must be an integer in ticks or millitiles."""
    if key in INT_NAMES or INT_SUFFIX.search(key):
        return True
    segments = re.sub(r"\[\d+\]", "", path).split(".")
    return any(seg.endswith(("_ticks", "_millitiles")) for seg in segments[:-1])


def is_number(value):
    return isinstance(value, (int, float)) and not isinstance(value, bool)


@pytest.fixture(scope="module", params=all_data_names())
def data_file(request):
    return request.param, load_data_file(request.param)


def test_unit_fields_are_python_ints(data_file):
    name, data = data_file
    bad = [(p, v) for p, k, v in walk(data) if is_number(v) and is_unit_path(p, k) and type(v) is not int]
    assert not bad, f"{name}.json has non-integer unit fields: {bad}"


def test_floats_only_appear_in_human_readable_fields(data_file):
    name, data = data_file
    bad = [(p, v) for p, k, v in walk(data) if isinstance(v, float) and not FLOAT_OK.search(k)]
    assert not bad, f"{name}.json has floats outside *_s, *_tiles, *_percent fields: {bad}"


def test_no_placeholder_nulls_in_unit_fields(data_file):
    name, data = data_file
    nulls = [p for p, k, v in walk(data) if v is None and is_unit_path(p, k)]
    assert not nulls, f"{name}.json still has null placeholders: {nulls}"


def _dicts(obj):
    if isinstance(obj, dict):
        yield obj
        for v in obj.values():
            yield from _dicts(v)
    elif isinstance(obj, list):
        for v in obj:
            yield from _dicts(v)


def test_seconds_agree_with_ticks(data_file):
    name, data = data_file
    for d in _dicts(data):
        for key, seconds in d.items():
            if key.endswith("_s") and is_number(seconds):
                ticks_key = key[:-2] + "_ticks"
                if isinstance(d.get(ticks_key), int):
                    expected = round(seconds * TICKS_PER_SECOND)
                    assert d[ticks_key] == expected, f"{name}.json {key}={seconds} but {ticks_key}={d[ticks_key]}"


def test_tiles_agree_with_millitiles(data_file):
    name, data = data_file
    for d in _dicts(data):
        for key, tiles in d.items():
            if key.endswith("_tiles") and is_number(tiles):
                milli_key = key[:-6] + "_millitiles"
                if isinstance(d.get(milli_key), int):
                    assert d[milli_key] == round(tiles * TILE_MILLITILES), f"{name}.json {key} vs {milli_key}"