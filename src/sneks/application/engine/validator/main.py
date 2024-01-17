import pytest

from sneks.application.engine.config.config import config


def main(test_path: str = None) -> int:
    if test_path is not None:
        config.registrar_prefix = test_path
    return pytest.main(["--pyargs", "sneks.validator"])
