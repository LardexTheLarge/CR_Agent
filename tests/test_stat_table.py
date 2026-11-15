"""Phase 2 done-check: print a clean stat table for the 8 cards, all values integers."""
from sim.data import DECK_CARD_IDS
from sim.stat_table import MISSING, NOT_APPLICABLE, build_rows, format_table


def test_stat_table_prints_and_every_value_is_an_integer(deck, capsys):
    rows = build_rows(deck)
    with capsys.disabled():           # show the table even without `pytest -s`
        print("\n" + format_table(rows))

    primary = [r for r in rows if not r.is_sub]
    assert len(primary) == len(DECK_CARD_IDS) == 8

    problems = []
    for row in rows:
        for col, cell in row.cells.items():
            if cell == MISSING:
                problems.append(f"{row.label.strip()}.{col} is null")
            elif cell != NOT_APPLICABLE and type(cell) is not int:
                problems.append(f"{row.label.strip()}.{col} = {cell!r} is not an integer")
    assert not problems, problems


def test_every_troop_row_has_hp_speed_and_range(deck):
    for row in build_rows(deck):
        if row.cells["hp"] != NOT_APPLICABLE and row.cells["speed"] != NOT_APPLICABLE:
            assert row.cells["hp"] > 0 and row.cells["speed"] > 0 and row.cells["range"] > 0, row.label