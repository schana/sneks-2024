import random

from sneks.application.engine.core.direction import Direction
from sneks.application.engine.interface.snek import Snek


class CustomSnek(Snek):
    def get_next_direction(self) -> Direction:
        directions = [Direction.UP, Direction.LEFT, Direction.RIGHT, Direction.DOWN]
        random.shuffle(directions)
        result = max(directions, key=lambda direction: self.look(direction))
        return result
