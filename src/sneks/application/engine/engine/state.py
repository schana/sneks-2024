import itertools
import random
from collections import Counter
from operator import methodcaller
from typing import FrozenSet, List, Set

from sneks.application.engine.config.config import config
from sneks.application.engine.core import board
from sneks.application.engine.core.cell import Cell
from sneks.application.engine.engine import registrar
from sneks.application.engine.engine.mover import Mover, NormalizedScore, Score


class State:
    cells: Set[Cell] = {
        Cell(r, c)
        for r, c in itertools.product(range(board.ROWS), range(board.COLUMNS))
    }
    food: Set[Cell] = set()
    active_snakes: List[Mover] = []
    ended_snakes: List[Mover] = []
    steps: int = 0

    def reset(self):
        self.steps = 0
        self.active_snakes = []
        self.ended_snakes = []
        self.food = set()
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
        for _ in range(
            len(self.active_snakes) if config.game.dynamic_food else config.game.food
        ):
            self.food.add(self.get_random_free_cell())
        self.set_board()

    def report(self) -> List[NormalizedScore]:
        scores = [
            s.get_score()
            for s in itertools.chain(self.active_snakes, self.ended_snakes)
        ]
        min_age = min(s.age for s in scores)
        max_age = max(s.age for s in scores)
        min_length = min(s.length for s in scores)
        max_length = max(s.length for s in scores)
        min_ended = min(s.ended for s in scores)
        max_ended = max(s.ended for s in scores)

        min_score = Score(name="min", age=min_age, length=min_length, ended=min_ended)
        max_score = Score(
            name="max",
            age=max(min_age + 1, max_age),
            length=max(min_length + 1, max_length),
            ended=max(min_ended + 1, max_ended),
        )

        normalized = [
            s.normalize(min_score=min_score, max_score=max_score) for s in scores
        ]
        normalized.sort(key=methodcaller("total"), reverse=True)

        return normalized

    def get_random_free_cell(self):
        options = self.cells.difference(self.get_occupied_cells()).difference(self.food)
        if options:
            return random.choice(tuple(options))
        else:
            return None

    def get_occupied_cells(self, snakes: List[Mover] | None = None) -> FrozenSet[Cell]:
        if snakes is None:
            values = itertools.chain(self.active_snakes, self.ended_snakes)
            return frozenset(itertools.chain(*(s.cells for s in values)))
        else:
            return frozenset(itertools.chain(*(s.cells for s in snakes)))

    def count_occupied_cells(self) -> Counter:
        return Counter(itertools.chain(*(s.cells for s in self.active_snakes)))

    def set_board(self):
        occupied = self.get_occupied_cells()
        for current_snake in self.active_snakes:
            current_snake.snek.body = list(current_snake.cells)
            current_snake.snek.food = frozenset(self.food)
            current_snake.snek.occupied = occupied.copy()

    def should_continue(self, turn_limit):
        return self.steps < turn_limit and self.active_snakes

    def end_snake(self, snake):
        self.active_snakes.remove(snake)
        self.ended_snakes.append(snake)

    def step(self):
        # move the heads
        for snake in self.active_snakes:
            snake.move()

        # pop the tails unless food is eaten
        for snake in self.active_snakes:
            snake.move_tail(food=self.food)

        # replace eaten food
        for snake in self.active_snakes:
            if snake.get_head() in self.food:
                self.food.remove(snake.get_head())
                if not config.game.dynamic_food or len(self.food) < len(
                    self.active_snakes
                ):
                    next_food = self.get_random_free_cell()
                    if next_food:
                        self.food.add(next_food)

        occupations = self.count_occupied_cells()
        ended_cells = self.get_occupied_cells(self.ended_snakes)

        to_end = []
        # determine ended snakes
        for snake in self.active_snakes:
            if not snake.get_head().is_valid():
                to_end.append(snake)
            elif snake.get_head() in ended_cells:
                to_end.append(snake)
            elif occupations[snake.get_head()] > 1:
                to_end.append(snake)

        for snake in to_end:
            self.end_snake(snake)

        # score alive snakes
        for snake in self.active_snakes:
            for cell in snake.cells:
                if (
                    occupations[cell] > 1 and cell is not snake.get_head()
                ):  # second part should be guaranteed
                    snake.ended += 1
            snake.age += 1

        self.set_board()
        self.steps += 1
