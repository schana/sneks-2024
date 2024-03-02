import math

from sneks.engine.config.instantiation import config
from sneks.engine.core.cell import Cell
from sneks.engine.core.direction import Direction


def get_absolute_neighbor(cell: Cell, direction: Direction) -> Cell:
    row_offset, column_offset = 0, 0
    if direction is Direction.UP:
        row_offset = -1
    elif direction is Direction.DOWN:
        row_offset = 1
    elif direction is Direction.LEFT:
        column_offset = -1
    elif direction is Direction.RIGHT:
        column_offset = 1
    else:
        raise ValueError("direction not valid")
    return Cell(
        (cell.row + row_offset) % config.game.rows,
        (cell.column + column_offset) % config.game.columns,
    )


def get_relative_to(cell: Cell, other: Cell) -> Cell:
    """
    Returns the relative cell in relation to "other". Other is likely the head when this is called,
    since that's what the coordinates are referenced on for the snek implementation.
    """
    return Cell(
        int(math.fmod((cell.row - other.row), config.game.rows)),
        int(math.fmod((cell.column - other.column), config.game.columns)),
    )
