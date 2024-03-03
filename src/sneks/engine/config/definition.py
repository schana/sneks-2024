from dataclasses import dataclass, field
from typing import List, Tuple


@dataclass
class Game:
    rows: int = 60
    columns: int = 90
    vision_range: int = 20


@dataclass
class Colors:
    background: Tuple[int, int, int] = (25, 28, 26)
    border: Tuple[int, int, int] = (113, 121, 113)
    invalid: Tuple[int, int, int] = (186, 26, 26)
    snake: List[Tuple[int, int, int]] = field(
        default_factory=lambda: [
            (222, 97, 116),
            (221, 65, 82),
            (223, 83, 51),
            (215, 117, 85),
            (231, 131, 31),
            (192, 123, 49),
            (194, 141, 80),
            (203, 149, 43),
            (223, 187, 36),
            (212, 189, 95),
            (150, 135, 41),
            (134, 124, 51),
            (186, 182, 59),
            (190, 190, 111),
            (174, 202, 41),
            (21, 149, 43),
            (54, 198, 76),
            (15, 145, 62),
            (124, 197, 56),
            (141, 197, 105),
            (63, 146, 47),
            (83, 188, 69),
            (128, 194, 121),
            (79, 201, 101),
            (60, 139, 73),
            (72, 208, 129),
            (78, 187, 130),
            (67, 194, 158),
            (54, 222, 230),
            (102, 161, 229),
            (92, 138, 228),
            (87, 127, 240),
            (121, 130, 206),
            (131, 106, 238),
            (159, 121, 219),
            (194, 134, 210),
            (192, 100, 217),
            (217, 69, 194),
            (212, 91, 184),
            (215, 122, 182),
            (222, 85, 144),
        ]
    )


@dataclass
class Graphics:
    display: bool = True
    headless: bool = False
    cell_size: int = 8
    padding: int = 1
    step_delay: int = 40
    step_keypress_wait: bool = False
    end_delay: int = 1000
    end_keypress_wait: bool = False
    record: bool = False
    record_prefix: str = "./output"
    colors: Colors = field(default_factory=Colors)


@dataclass
class Config:
    game: Game = field(default_factory=Game)
    graphics: Graphics = field(default_factory=Graphics)
    runs: int = 10
    turn_limit: int = 1000
    registrar_prefix: str = "src"
    registrar_submission_sneks: int = 1
