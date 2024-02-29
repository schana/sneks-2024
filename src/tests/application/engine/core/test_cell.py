from sneks.application.engine.config.config import config
from sneks.application.engine.core.cell import Cell
from sneks.application.engine.core.direction import Direction
from sneks.application.engine.engine import cells


def test_cell() -> None:
    absolute = Cell(0, 0)
    head = Cell(0, 20)

    assert cells.get_relative_to(absolute, head) == Cell(0, -20)

    assert absolute.get_neighbor(Direction.UP) == Cell(-1, 0)

    assert absolute.get_distance(Cell(0, config.game.columns - 1)) == 1

    assert Cell(0, -1) == Cell(0, config.game.columns - 1)

    assert Cell(-1, 0) in (Cell(config.game.rows - 1, 0),)
