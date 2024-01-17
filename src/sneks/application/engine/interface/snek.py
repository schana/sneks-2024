import abc
from typing import FrozenSet, List, Sequence

from sneks.application.engine.core.board import COLUMNS, ROWS
from sneks.application.engine.core.cell import Cell
from sneks.application.engine.core.direction import Direction


class Snek(abc.ABC):
    """
    Base snek from which submission sneks derive. This snek has no behavior,
    but derivations should implement ``get_next_direction()`` to provide it.
    """

    #: Body of the snek represented as a list of cells, with index 0 being the head
    body: List[Cell] = []
    #: Set of currently occupied cells on the game board
    occupied: FrozenSet[Cell] = frozenset()
    #: Set of cells that contain food on the game board
    food: FrozenSet[Cell] = frozenset()

    def get_next_direction(self) -> Direction:
        """
        Method that determines which way the snek should go next.

        :return: the next direction for the snek to move
        """
        raise NotImplementedError()

    def get_head(self) -> Cell:
        """
        Helper method to return the first cell from the snek's body.

        :return: the cell representing the head of the snake
        """
        return self.body[0]

    def get_body(self) -> List[Cell]:
        """
        Helper method to return the snek's body.

        :return: the list of cells making up the snake, including the head
        """
        return self.body

    def get_occupied(self) -> FrozenSet[Cell]:
        """
        Helper method to return all occupied cells on the board. This
        includes both cells from your snek's body and all other sneks'
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

    def get_rows(self) -> int:
        """
        Helper method to return the number of rows in the game board.

        :return: the number of rows in the game board
        """
        return ROWS

    def get_columns(self) -> int:
        """
        Helper method to return the number of columns in the game board.

        :return: the number of columns in the game board
        """
        return COLUMNS

    def get_food(self) -> FrozenSet[Cell]:
        """
        Helper method to return the current food on the board.

        :return: the set of food on the game board
        """
        return self.food

    def get_closest_food(self) -> Cell:
        """
        Get the closest food to the head of the snek from the current set.

        :return: the Cell representing the location of the nearest food
        """
        return min(self.food, key=lambda food: food.get_distance(self.get_head()))

    def look(self, direction: Direction) -> int:
        """
        Look in a direction from the snek's head and get the distance to the closest obstacle.
        An obstacle could either be an occupied cell or the game board's border.

        >>> self.get_head()  # the head is in the upper left corner of the board
        Cell(0, 0)
        >>> self.look(Direction.LEFT)
        0

        :param direction: the direction to look
        :return: the distance until the closest obstacle in the specified direction
        """

        current = self.get_head().get_neighbor(direction)
        current_distance = 1

        while current not in self.occupied and current.is_valid():
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
        most distance between itself and the closest food, this method could be
        used like::

            self.get_direction_to_destination(self.get_closest_food())

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
