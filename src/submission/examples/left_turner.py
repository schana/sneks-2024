from sneks.engine.core.direction import Direction
from sneks.engine.interface.snek import Snek


class CustomSnek(Snek):
    """
    This Snek turns left every four moves
    """

    directions = [Direction.UP, Direction.LEFT, Direction.DOWN, Direction.RIGHT]
    moves = 0

    def get_next_direction(self) -> Direction:
        self.moves += 1
        direction_index = (self.moves // 4) % len(self.directions)
        return self.directions[direction_index]
