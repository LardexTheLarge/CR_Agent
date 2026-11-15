import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from sim.data import load_arena, load_deck, load_tower  # noqa: E402


@pytest.fixture(scope="session")
def deck():
    return load_deck()


@pytest.fixture(scope="session")
def towers():
    return {"king_tower": load_tower("king_tower"), "princess_tower": load_tower("princess_tower")}


@pytest.fixture(scope="session")
def arena():
    return load_arena()