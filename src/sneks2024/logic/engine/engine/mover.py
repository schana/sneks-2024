from collections import deque
from dataclasses import dataclass
from typing import Set, Tuple

from sneks.core.cell import Cell
from sneks.interface.snek import Snek


@dataclass(frozen=True)
class NormalizedScore:
    age: float
    length: float
    ended: float
    raw: "Score"

    def total(self) -> float:
        return self.age + self.length + self.ended

    def __repr__(self):
        return (
            f"age': {self.age:.4f}, length': {self.length:.4f}, ended': {self.ended:.4f}, "
            f"age: {self.raw.age:4d}, length: {self.raw.length:2d}, ended: {self.raw.ended:2d}, "
            f"name: {self.raw.name}"
        )


@dataclass(frozen=True)
class Score:
    name: str
    age: int
    length: int
    ended: int

    def normalize(self, min_score: "Score", max_score: "Score") -> NormalizedScore:
        return NormalizedScore(
            age=(self.age - min_score.age) / (max_score.age - min_score.age),
            length=(self.length - min_score.length)
            / (max_score.length - min_score.length),
            ended=(self.ended - min_score.ended) / (max_score.ended - min_score.ended),
            raw=self,
        )


class Mover:
    def __init__(self, name: str, head: Cell, snek: Snek, color: Tuple[int, int, int]):
        self.name = name
        self.cells = deque([head])
        self.snek = snek
        self.age = 0
        self.color = color
        self.ended = 0

    def get_head(self) -> Cell:
        return self.cells[0]

    def move(self):
        next_direction = self.snek.get_next_direction()
        next_head = self.get_head().get_neighbor(next_direction)
        self.cells.appendleft(next_head)

    def move_tail(self, food: Set[Cell]):
        if not self.get_head() in food:
            self.cells.pop()

    def get_score(self) -> Score:
        return Score(
            name=self.name, age=self.age, length=len(self.cells), ended=self.ended
        )
