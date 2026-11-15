"""Builds the clean stat table for the 8 deck cards (run: python -m sim.stat_table)."""
from __future__ import annotations

from dataclasses import dataclass

from sim.data import DECK_CARD_IDS, DataError, get_path, load_deck

NOT_APPLICABLE = "-"
MISSING = "?"

COLUMNS = (
    ("elixir", "Elix"),
    ("units", "Units"),
    ("hp", "HP"),
    ("damage", "Damage"),
    ("hit_ticks", "Hit t"),
    ("first_hit_ticks", "1stHit t"),
    ("range", "Range mt"),
    ("speed", "Speed mt/t"),
    ("deploy_ticks", "Deploy t"),
    ("radius", "Radius mt"),
    ("mass", "Mass"),
    ("life_ticks", "Life t"),
    ("delay_ticks", "Delay t"),
)


def _row(**refs):
    """Column -> data path (str), literal int, or None for not applicable."""
    return {key: refs.get(key) for key, _ in COLUMNS}


def _unit(prefix: str, *, elixir=None, units=1, deploy=True):
    return _row(
        elixir=elixir, units=units,
        hp=f"{prefix}.hitpoints", damage=f"{prefix}.damage",
        hit_ticks=f"{prefix}.hit_speed_ticks", first_hit_ticks=f"{prefix}.first_hit_ticks",
        range=f"{prefix}.range_millitiles", speed=f"{prefix}.speed_millitiles_per_tick",
        deploy_ticks=f"{prefix}.deploy_time_ticks" if deploy else None, radius=f"{prefix}.collision_radius_millitiles",
        mass=f"{prefix}.mass",
    )


def _troop():
    return _unit("base", elixir="base.elixir", units="base.unit_count")


# (label, is_sub_row, column spec). Spells show their area radius under Radius and their
# impact (Arrows) or launch (Barrel) delay under Delay. Little Prince shows stage 1 hit speed.
SPEC = {
    "royal_recruits": [("Royal Recruits", False, _troop())],
    "little_prince": [
        ("Little Prince", False, {**_troop(), "hit_ticks": "attack_ramp.stages[0].hit_speed_ticks"}),
        ("  Guardian", True, _unit("guardian")),
    ],
    "goblin_cage": [
        ("Goblin Cage", False, _row(
            elixir="base.elixir", units=1, hp="base.hitpoints", deploy_ticks="base.deploy_time_ticks",
            radius="base.collision_radius_millitiles", life_ticks="base.lifetime_ticks")),
        ("  Goblin Brawler", True, _unit("goblin_brawler", deploy=False)),
    ],
    "flying_machine": [("Flying Machine", False, _troop())],
    "zappies": [("Zappies", False, _troop())],
    "royal_hogs": [("Royal Hogs", False, _troop())],
    "arrows": [("Arrows", False, _row(
        elixir="base.elixir", units=1, damage="base.total_damage",
        radius="base.radius_millitiles", delay_ticks="timing.impact_delay_ticks"))],
    "barbarian_barrel": [
        ("Barbarian Barrel", False, _row(
            elixir="base.elixir", units=1, damage="base.damage", range="base.roll_distance_millitiles",
            speed="base.roll_speed_millitiles_per_tick", radius="base.radius_millitiles",
            delay_ticks="base.launch_delay_ticks")),
        ("  Barbarian", True, _unit("spawned_unit", deploy=False)),
    ],
}


@dataclass(frozen=True)
class Row:
    label: str
    is_sub: bool
    cells: dict


def _cell(card: dict, ref, where: str):
    if ref is None:
        return NOT_APPLICABLE
    if isinstance(ref, int):
        return ref
    value = get_path(card, ref, where=where)
    return MISSING if value is None else value


def build_rows(deck: dict[str, dict] | None = None) -> list[Row]:
    deck = deck if deck is not None else load_deck()
    rows = []
    for card_id in DECK_CARD_IDS:
        for label, is_sub, spec in SPEC[card_id]:
            cells = {col: _cell(deck[card_id], spec[col], f"{card_id}.json") for col, _ in COLUMNS}
            rows.append(Row(label, is_sub, cells))
    return rows


def format_table(rows: list[Row]) -> str:
    headers = ["Card"] + [title for _, title in COLUMNS]
    body = [[r.label] + [str(r.cells[col]) for col, _ in COLUMNS] for r in rows]
    widths = [max(len(h), *(len(line[i]) for line in body)) for i, h in enumerate(headers)]

    def fmt(line):
        return "  ".join(
            (cell.ljust(w) if i == 0 else cell.rjust(w)) for i, (cell, w) in enumerate(zip(line, widths))
        )

    rule = "  ".join("-" * w for w in widths)
    out = [fmt(headers), rule]
    out += [fmt(line) for line in body]
    primary = [r for r in rows if not r.is_sub]
    elixir_total = sum(r.cells["elixir"] for r in primary if isinstance(r.cells["elixir"], int))
    out += [
        rule,
        f"Deck: {len(primary)} cards, average elixir {elixir_total / len(primary):.1f}",
        "Units: times in 50 ms ticks (t), distances in millitiles (mt), speed in mt per tick.",
        "Spells: Radius is the area radius; Delay is the impact (Arrows) or launch (Barrel) delay.",
        "'-' = not applicable, '?' = field exists but is still null.",
    ]
    return "\n".join(out)


def main() -> None:
    try:
        print(format_table(build_rows()))
    except DataError as exc:
        raise SystemExit(f"data error: {exc}")


if __name__ == "__main__":
    main()