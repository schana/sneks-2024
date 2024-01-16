from sneks.config.config import config
from sneks.core.cell import Cell
from sneks.core.direction import Direction
from sneks.engine import registrar, runner
from sneks.engine.mover import NormalizedScore
from sneks.interface.snek import Snek


def test_basic_functionality():
    submissions = registrar.get_submissions()
    assert 1 == len(submissions)
    snek: Snek = submissions[0].snek
    snek.food = frozenset((Cell(0, 0),))
    snek.occupied = frozenset((Cell(1, 1),))
    snek.body = [Cell(1, 1)]
    assert snek.get_next_direction() in Direction


def test_extended_functionality():
    config.graphics.display = False
    config.turn_limit = 100
    scores = runner.main()
    assert len(scores) == 10
    for score in scores:
        assert isinstance(score, NormalizedScore)
        assert score.age == 0
        assert score.length == 0
        assert score.ended == 0
        assert score.raw.age >= 0
        assert score.raw.length >= 1
        assert score.raw.ended == 0


def test_multiple_functionality():
    config.graphics.display = False
    config.registrar_submission_sneks = 100
    scores = runner.main()
    assert len(scores) == 1000
    for score in scores:
        assert isinstance(score, NormalizedScore)
        assert 0 <= score.age <= 1
        assert 0 <= score.length <= 1
        assert 0 <= score.ended <= 1
        assert score.raw.age >= 0
        assert score.raw.length >= 1
        assert score.raw.ended >= 0
