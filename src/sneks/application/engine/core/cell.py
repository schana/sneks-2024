import math
from dataclasses import dataclass

try:
    from functools import cache
except ImportError:
    from functools import lru_cache as cache

from sneks.application.engine.config.config import config
from sneks.application.engine.core.direction import Direction


@dataclass(frozen=True)
class Cell:
    """
    Represents a single cell on the game board. They can be used as reference points
    for getting neighboring cells, like:

    >>> cell = Cell(1, 1)
    >>> cell.get_left()
    Cell(1, 0)
    >>> cell.get_relative_neighbor(2, 3)
    Cell(3, 4)
    >>> cell.get_neighbor(Direction.DOWN)
    Cell(2, 1)

    Also, it can be used to check game board boundaries, like:

    >>> cell = Cell(1, 1)
    >>> cell.is_valid()
    True
    >>> cell = Cell(-1, 0)
    >>> cell.is_valid()
    False

    Finally, it can be used to calculate distance between cells:

    >>> cell_a = Cell(0, 0)
    >>> cell_b = Cell(1, 0)
    >>> cell_a.get_distance(cell_b)
    1.0

    """

    row: int  #:
    column: int  #:

    @cache  # type: ignore
    def __new__(cls, row: int, column: int) -> "Cell":
        return super().__new__(cls)

    def __getnewargs__(self):
        return self.row, self.column

    def get_relative_neighbor(self, row_offset: int, column_offset: int) -> "Cell":
        """
        Returns the cell with coordinates offset by the specified parameters.

        :param row_offset: the amount to offset this cell's row by
        :param column_offset: the amount to offset this cell's column by
        :return: the cell at ``(self.row + row_offset, self.column + column_offset)``
        """
        return Cell(self.row + row_offset, self.column + column_offset)

    def get_neighbor(self, direction: Direction) -> "Cell":
        """
        Gets a Cell's neighbor in the specified direction. Note that this does
        not perform any boundary checking and could return invalid cells.

        :param direction: the direction of the neighbor
        :return: the neighbor cell in the specified direction
        """
        if direction is Direction.UP:
            return self.get_up()
        elif direction is Direction.DOWN:
            return self.get_down()
        elif direction is Direction.LEFT:
            return self.get_left()
        elif direction is Direction.RIGHT:
            return self.get_right()
        else:
            raise ValueError("direction not valid")

    def get_up(self) -> "Cell":
        """
        :return: cell in the up direction
        """
        return self.get_relative_neighbor(-1, 0)

    def get_down(self) -> "Cell":
        """
        :return: cell in the down direction
        """
        return self.get_relative_neighbor(1, 0)

    def get_left(self) -> "Cell":
        """
        :return: cell in the left direction
        """
        return self.get_relative_neighbor(0, -1)

    def get_right(self) -> "Cell":
        """
        :return: cell in the right direction
        """
        return self.get_relative_neighbor(0, 1)

    def get_distance(self, other: "Cell") -> float:
        """
        Gets the distance between this cell and another.

        :param other: cell to get distance to
        :return: distance between the two cells
        """
        return math.hypot(self.column - other.column, self.row - other.row)

    def is_valid(self) -> bool:
        """
        Checks if this cell is within the game board.

        :return: True if the cell is in the board, False otherwise
        """
        return (
            0 <= self.row < config.game.rows and 0 <= self.column < config.game.columns
        )
