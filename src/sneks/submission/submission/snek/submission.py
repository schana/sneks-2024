from sneks.application.engine.core.direction import Direction
from sneks.application.engine.interface.snek import Snek


class CustomSnek(Snek):
    def get_next_direction(self) -> Direction:
        return Direction.UP
