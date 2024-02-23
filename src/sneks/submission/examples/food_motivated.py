from sneks.application.engine.core.cell import Cell
from sneks.application.engine.core.direction import Direction
from sneks.application.engine.interface.snek import Snek


class CustomSnek(Snek):
    """
    This Snek moves towards the closest food without regard for obstacles
    """

    def get_next_direction(self) -> Direction:
        closest_food: Cell = min(
            self.get_food(), key=lambda food: self.get_head().get_distance(food)
        )
        return self.get_direction_to_destination(destination=closest_food)
