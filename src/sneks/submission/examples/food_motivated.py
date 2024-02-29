from sneks.application.engine.core.direction import Direction
from sneks.application.engine.interface.snek import Snek


class CustomSnek(Snek):
    """
    This Snek moves towards the closest food without regard for obstacles
    """

    # TODO: fix this

    def get_next_direction(self) -> Direction:
        return Direction.RIGHT
