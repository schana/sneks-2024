import abc
from typing import FrozenSet, Sequence

from sneks.engine.config.instantiation import config
from sneks.engine.core.cell import Cell
from sneks.engine.core.direction import Direction


class Snek(abc.ABC):
    """
    Base snek from which submission sneks derive. This snek has no behavior,
    but derivations should implement ``get_next_direction()`` to provide it.
    """

    #: Head snek represented as Cell
    head: Cell = Cell(0, 0)
    #: Set of currently occupied cells on the game board
    occupied: FrozenSet[Cell] = frozenset()

    def get_next_direction(self) -> Direction:
        """
        Method that determines which way the snek should go next.

        :return: the next direction for the snek to move
        """
        raise NotImplementedError()

    def get_head(self) -> Cell:
        """
        Helper method to return the head of the snek.

        :return: the cell representing the head of the snek
        """
        return self.head

    def get_occupied(self) -> FrozenSet[Cell]:
        """
        Helper method to return all occupied cells that the snek can see.
        This includes both cells from your snek's body and all other sneks'
        bodies.

        This can be used in your ``get_next_direction()`` to check if a cell
        you are planning on moving to is already taken. Example::

            potential_next_cell = self.get_head().get_up()
            if potential_next_cell in self.get_occupied():
                # potential_next_cell is already taken
            else:
                # potential_next_cell is free

        :return: the set of occupied cells on the game board
        """
        return self.occupied

    def look(self, direction: Direction) -> int:
        """
        Look in a direction from the snek's head and get the distance to the closest obstacle.
        An obstacle could either be an occupied cell or the game board's border.

        >>> self.get_head()
        Cell(0, 0)
        >>> self.look(Direction.LEFT)
        0

        :param direction: the direction to look
        :return: the distance until the closest obstacle in the specified direction
        """

        current = self.get_head().get_neighbor(direction)
        current_distance = 1

        while (
            current not in self.occupied
            and current_distance <= config.game.vision_range
        ):
            current = current.get_neighbor(direction)
            current_distance += 1

        return current_distance - 1

    def get_direction_to_destination(
        self,
        destination: Cell,
        directions: Sequence[Direction] = (
            Direction.UP,
            Direction.DOWN,
            Direction.LEFT,
            Direction.RIGHT,
        ),
    ) -> Direction:
        """
        Get the next direction to travel in order to reach the destination
        from a set of specified directions (default: all directions).

        When multiple directions have the same resulting distance, the chosen
        direction is determined by the order provided, with directions coming
        first having precedence.

        For example, to get the direction the snek should travel to close the
        most distance between itself and a cell 5 rows and 9 columns away,
        this method could be used like::

            self.get_direction_to_destination(Cell(5, 9))

        :param destination: the cell to travel towards
        :param directions: the directions to evaluate in order
        :return: the direction to travel that will close the most distance
        """

        return min(
            directions,
            key=lambda direction: self.get_head()
            .get_neighbor(direction)
            .get_distance(destination),
        )
