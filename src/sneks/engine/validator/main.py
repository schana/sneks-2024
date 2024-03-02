import pytest

from sneks.engine.config.instantiation import config


def main(test_path: str | None = None) -> int:
    if test_path is not None:
        config.registrar_prefix = test_path
    return pytest.main(["--pyargs", "sneks.engine.validator"])
