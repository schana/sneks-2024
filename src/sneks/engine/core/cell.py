import math
from dataclasses import dataclass
from functools import cache, cached_property

from sneks.engine.config.instantiation import config
from sneks.engine.core.direction import Direction


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

    @cached_property
    def _hash(self):
        # Determine the hash based on only positive indices,
        # so hash(Cell(-1,-1)) == hash(Cell(rows, columns))
        return hash((self.row % config.game.rows, self.column % config.game.columns))

    def __eq__(self, other):
        return self._hash == other._hash

    def __hash__(self):
        return self._hash

    @cache
    def get_relative_neighbor(self, row_offset: int, column_offset: int) -> "Cell":
        """
        Returns the cell with coordinates offset by the specified parameters.

        :param row_offset: the amount to offset this cell's row by
        :param column_offset: the amount to offset this cell's column by
        :return: the cell at ``(self.row + row_offset, self.column + column_offset)``
        """
        # We need to use integer modulus instead of floor to use the sign
        # of the numerator as opposed to the denominator in order to preserve
        # the relative direction of the Cell
        # Effectively: n - int(n / base) * base
        # Instead of:  n - floor(n / base) * base
        return Cell(
            int(math.fmod((self.row + row_offset), config.game.rows)),
            int(math.fmod((self.column + column_offset), config.game.columns)),
        )

    def get_neighbor(self, direction: Direction) -> "Cell":
        """
        Gets a Cell's neighbor in the specified direction. Note that this does
        not perform any boundary checking and could return invalid cells.

        :param direction: the direction of the neighbor
        :return: cell in the specified direction
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

        # Get raw distance
        column_distance = abs(self.column - other.column)
        row_distance = abs(self.row - other.row)

        # Determine if it's closer to go the other way
        column_distance = (
            column_distance
            if column_distance < config.game.columns / 2
            else config.game.columns - column_distance
        )
        row_distance = (
            row_distance
            if row_distance < config.game.rows / 2
            else config.game.rows - row_distance
        )

        # Compute the distance
        return math.sqrt(column_distance**2 + row_distance**2)
