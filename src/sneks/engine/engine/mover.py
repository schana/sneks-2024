from dataclasses import dataclass
from typing import Tuple

from sneks.engine.core.cell import Cell
from sneks.engine.engine import cells
from sneks.engine.interface.snek import Snek


@dataclass(frozen=True)
class NormalizedScore:
    age: float
    ended: float
    raw: "Score"

    def total(self) -> float:
        return self.age + self.ended

    def __repr__(self):
        return (
            f"age': {self.age:.4f}, ended': {self.ended:.4f}, "
            f"age: {self.raw.age:4d}, ended: {self.raw.ended:2d}, "
            f"name: {self.raw.name}"
        )


@dataclass(frozen=True)
class Score:
    name: str
    age: int
    ended: int

    def normalize(self, min_score: "Score", max_score: "Score") -> NormalizedScore:
        return NormalizedScore(
            age=(self.age - min_score.age) / (max_score.age - min_score.age),
            ended=(self.ended - min_score.ended) / (max_score.ended - min_score.ended),
            raw=self,
        )


class Mover:
    def __init__(self, name: str, head: Cell, snek: Snek, color: Tuple[int, int, int]):
        self.name = name
        self.head = head
        self.cells = {head}
        self.body = [head]
        self.snek = snek
        self.age = 0
        self.color = color
        self.ended = 0

    def get_head(self) -> Cell:
        return self.head

    def move(self):
        next_direction = self.snek.get_next_direction()
        next_head = cells.get_absolute_neighbor(self.get_head(), next_direction)
        self.cells.add(next_head)
        self.body.append(next_head)
        self.head = next_head

    def get_score(self) -> Score:
        return Score(name=self.name, age=self.age, ended=self.ended)
