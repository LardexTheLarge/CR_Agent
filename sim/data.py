"""Loader and helpers for the card, tower and arena JSON files (Phase 2 data layer).

Every file under the data directory is plain JSON. Times are integer ticks (50 ms) and
distances are integer millitiles (1 tile = 1000). Human-readable fields (*_s, *_tiles)
sit beside the integer fields for checking, and tests keep the two consistent.

The data directory is ``<repo>/data`` unless the CR_DATA_DIR environment variable is set.
Files are found by name anywhere below it, so a flat or nested layout both work.
"""
from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import Any, Iterator

REPO_ROOT = Path(__file__).resolve().parent.parent

TICK_MS = 50
TICKS_PER_SECOND = 1000 // TICK_MS
TILE_MILLITILES = 1000

DECK_CARD_IDS = (
    "royal_recruits",
    "little_prince",
    "goblin_cage",
    "flying_machine",
    "zappies",
    "royal_hogs",
    "arrows",
    "barbarian_barrel",
)
TOWER_IDS = ("king_tower", "princess_tower")
ARENA_ID = "arena"

SPEED_TIER_MT_PER_TICK = {"slow": 37, "medium": 50, "fast": 75, "very_fast": 100}
MELEE_RANGE_MILLITILES = {"melee_short": 800, "melee_medium": 1200, "melee_long": 1600}


class DataError(Exception):
    """A data file is missing, malformed, or lacks a field the code needs."""


def data_dir() -> Path:
    return Path(os.environ.get("CR_DATA_DIR", REPO_ROOT / "data"))


def find_data_file(name: str) -> Path:
    root = data_dir()
    matches = sorted(root.rglob(f"{name}.json"))
    if not matches:
        raise DataError(f"{name}.json not found under {root}")
    if len(matches) > 1:
        raise DataError(f"{name}.json is ambiguous, found {[str(m) for m in matches]}")
    return matches[0]


def load_data_file(name: str) -> dict:
    path = find_data_file(name)
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise DataError(f"{path.name} is not valid JSON: {exc}") from exc


def load_card(card_id: str) -> dict:
    return load_data_file(card_id)


def load_deck() -> dict[str, dict]:
    return {card_id: load_card(card_id) for card_id in DECK_CARD_IDS}


def load_tower(tower_id: str) -> dict:
    return load_data_file(tower_id)


def load_arena() -> dict:
    return load_data_file(ARENA_ID)


def all_data_names() -> tuple[str, ...]:
    return DECK_CARD_IDS + TOWER_IDS + (ARENA_ID,)


_TOKEN = re.compile(r"([^.\[\]]+)|\[(\d+)\]")


def get_path(data: Any, dotted: str, *, where: str = "") -> Any:
    """Read ``a.b[0].c`` from nested data. Raises DataError if any step is missing."""
    cur = data
    for key, index in _TOKEN.findall(dotted):
        try:
            cur = cur[int(index)] if index else cur[key]
        except (KeyError, IndexError, TypeError) as exc:
            raise DataError(f"{where}: missing field '{dotted}'") from exc
    return cur


def walk(obj: Any, path: str = "") -> Iterator[tuple[str, str, Any]]:
    """Yield (path, key, value) for every value in nested dicts and lists.

    For list items the key is the list's own key, so unit rules that look at the key
    (for example 'legal_cursor_x_millitiles') also apply to the items inside it.
    """
    if isinstance(obj, dict):
        for key, value in obj.items():
            child = f"{path}.{key}" if path else key
            yield child, key, value
            yield from walk(value, child)
    elif isinstance(obj, list):
        parent_key = re.sub(r"\[\d+\]$", "", path.rsplit(".", 1)[-1])
        for i, value in enumerate(obj):
            child = f"{path}[{i}]"
            if not isinstance(value, (dict, list)):
                yield child, parent_key, value
            yield from walk(value, child)