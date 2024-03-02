from sneks.engine.config.instantiation import config
from sneks.engine.core.cell import Cell
from sneks.engine.core.direction import Direction
from sneks.engine.engine import registrar, runner
from sneks.engine.engine.mover import NormalizedScore
from sneks.engine.interface.snek import Snek


def test_basic_functionality() -> None:
    submissions = registrar.get_submissions()
    assert 1 == len(submissions)
    snek: Snek = submissions[0].snek
    snek.occupied = frozenset((Cell(1, 1),))
    assert snek.get_next_direction() in Direction


def test_extended_functionality() -> None:
    assert config.graphics is not None
    config.graphics.display = False
    config.turn_limit = 100
    scores = runner.main()
    assert scores is not None
    assert len(scores) == 10
    for score in scores:
        assert isinstance(score, NormalizedScore)
        assert score.age == 0
        assert score.ended == 0
        assert score.raw.age >= 0
        assert score.raw.ended == 0


def test_multiple_functionality() -> None:
    assert config.graphics is not None
    config.graphics.display = False
    config.registrar_submission_sneks = 100
    scores = runner.main()
    assert scores is not None
    assert len(scores) == 1000
    for score in scores:
        assert isinstance(score, NormalizedScore)
        assert 0 <= score.age <= 1
        assert 0 <= score.ended <= 1
        assert score.raw.age >= 0
        assert score.raw.ended >= 0
