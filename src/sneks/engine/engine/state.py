import itertools
import random
from collections import Counter
from operator import methodcaller
from typing import FrozenSet, List, Set

from sneks.engine.config.instantiation import config
from sneks.engine.core.cell import Cell
from sneks.engine.engine import cells, registrar
from sneks.engine.engine.mover import Mover, NormalizedScore, Score


class State:
    def __init__(self):
        self.cells: Set[Cell] = {
            Cell(r, c)
            for r, c in itertools.product(
                range(config.game.rows), range(config.game.columns)
            )
        }
        self.active_snakes: List[Mover] = []
        self.ended_snakes: List[Mover] = []
        self.steps: int = 0
        self.occupied: set[Cell] = set()

    def reset(self):
        self.steps = 0
        self.active_snakes = []
        self.ended_snakes = []
        self.occupied = set()
        sneks = registrar.get_submissions()
        sneks.sort(key=lambda s: s.name)
        color_index = 0
        color_index_delta = max(len(config.graphics.colors.snake) // len(sneks), 1)
        for snek in sneks:
            self.active_snakes.append(
                Mover(
                    name=snek.name,
                    head=self.get_random_free_cell(),
                    snek=snek.snek,
                    color=config.graphics.colors.snake[color_index],
                )
            )
            color_index = (color_index + color_index_delta) % len(
                config.graphics.colors.snake
            )
        self.set_board()

    def score_sneks_ended(self) -> None:
        occupations = self.count_occupied_cells()
        for snake in itertools.chain(self.active_snakes, self.ended_snakes):
            for cell in snake.cells:
                if (
                    occupations[cell] > 1 and cell is not snake.get_head()
                ):  # second part should be guaranteed
                    snake.ended += 1

    def count_occupied_cells(self) -> Counter:
        values = itertools.chain(self.active_snakes, self.ended_snakes)
        return Counter(itertools.chain(*(s.cells for s in values)))

    def report(self) -> List[NormalizedScore]:
        self.score_sneks_ended()

        scores = [
            s.get_score()
            for s in itertools.chain(self.active_snakes, self.ended_snakes)
        ]
        min_age = min(s.age for s in scores)
        max_age = max(s.age for s in scores)
        min_ended = min(s.ended for s in scores)
        max_ended = max(s.ended for s in scores)

        min_score = Score(name="min", age=min_age, ended=min_ended)
        max_score = Score(
            name="max",
            age=max(min_age + 1, max_age),
            ended=max(min_ended + 1, max_ended),
        )

        normalized = [
            s.normalize(min_score=min_score, max_score=max_score) for s in scores
        ]
        normalized.sort(key=methodcaller("total"), reverse=True)

        return normalized

    def get_random_free_cell(self):
        options = self.cells.difference(self.get_occupied_cells())
        if options:
            return random.choice(tuple(options))
        else:
            return None

    def get_occupied_cells(self, snakes: List[Mover] | None = None) -> FrozenSet[Cell]:
        if snakes is None:
            values = itertools.chain(self.active_snakes, self.ended_snakes)
            return frozenset().union(*(s.cells for s in values))
        else:
            return frozenset().union(*(s.cells for s in snakes))

    def set_board(self):
        for current_snake in self.active_snakes:
            head = current_snake.get_head()

            # build a grid around the head based on the vision range
            grid = {
                Cell(r, c)
                for r, c in itertools.product(
                    range(
                        head.row - config.game.vision_range,
                        head.row + config.game.vision_range,
                    ),
                    range(
                        head.column - config.game.vision_range,
                        head.column + config.game.vision_range,
                    ),
                )
            }

            # set the snek's occupied to occupied cells within grid
            current_snake.snek.occupied = frozenset(
                cells.get_relative_to(cell, head)
                for cell in grid.intersection(self.occupied)
            )

    def should_continue(self, turn_limit):
        return self.steps < turn_limit and self.active_snakes

    def end_snake(self, snake):
        self.active_snakes.remove(snake)
        self.ended_snakes.append(snake)

    def step(self):
        # add previous head to occupied
        self.occupied |= {s.get_head() for s in self.active_snakes}

        # move the heads
        for snake in self.active_snakes:
            snake.move()

        occupations = Counter(s.get_head() for s in self.active_snakes)

        to_end = []
        # determine ended snakes
        for snake in self.active_snakes:
            if snake.get_head() in self.occupied:
                to_end.append(snake)
            elif occupations[snake.get_head()] > 1:
                to_end.append(snake)

        for snake in to_end:
            self.end_snake(snake)

        for snake in self.active_snakes:
            snake.age += 1

        self.set_board()
        self.steps += 1
