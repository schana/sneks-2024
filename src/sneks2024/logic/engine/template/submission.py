from sneks.core.direction import Direction
from sneks.interface.snek import Snek


class CustomSnek(Snek):
    def get_next_direction(self) -> Direction:
        return self.get_direction_to_destination(self.get_closest_food())
