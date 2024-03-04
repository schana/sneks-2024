import math

from sneks.engine.config.instantiation import config
from sneks.engine.core.cell import Cell
from sneks.engine.core.direction import Direction


def get_absolute_neighbor(cell: Cell, direction: Direction) -> Cell:
    x_offset, y_offset = 0, 0
    if direction is Direction.UP:
        y_offset = 1
    elif direction is Direction.DOWN:
        y_offset = -1
    elif direction is Direction.LEFT:
        x_offset = -1
    elif direction is Direction.RIGHT:
        x_offset = 1
    else:
        raise ValueError("direction not valid")
    return Cell(
        (cell.x + x_offset) % config.game.columns,
        (cell.y + y_offset) % config.game.rows,
    )


def get_relative_to(cell: Cell, other: Cell) -> Cell:
    """
    Returns the relative cell in relation to "other". Other is likely the head when this is called,
    since that's what the coordinates are referenced on for the snek implementation.
    """
    return Cell(
        int(math.fmod((cell.x - other.x), config.game.columns)),
        int(math.fmod((cell.y - other.y), config.game.rows)),
    )
