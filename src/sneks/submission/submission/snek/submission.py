import random

from sneks.engine.core.direction import Direction
from sneks.engine.interface.snek import Snek


class CustomSnek(Snek):
    def get_next_direction(self) -> Direction:
        directions = [Direction.UP, Direction.LEFT, Direction.RIGHT, Direction.DOWN]
        random.shuffle(directions)
        return max(directions, key=lambda direction: self.look(direction))
