import pathlib

from sneks.engine.config.instantiation import config
from sneks.engine.engine import registrar
from sneks.engine.interface.snek import Snek


def test_import():
    prefix = pathlib.Path(config.registrar_prefix)
    submission_files = registrar.get_submission_files(prefix)
    print(submission_files)
    assert 1 == len(submission_files)
    name = registrar.get_submission_name(submission_files[0])
    assert pathlib.Path(prefix, name, "submission.py").exists()
    registrar.load_module(prefix)

    submissions = registrar.get_submissions()
    assert 1 == len(submissions)
    assert name == submissions[0].name


def test_class_exists():
    _, snek = registrar.get_custom_snek(pathlib.Path(config.registrar_prefix))
    assert issubclass(snek, Snek)
