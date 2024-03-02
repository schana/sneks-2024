import importlib
import importlib.util
import pathlib
import sys
from dataclasses import dataclass
from importlib.machinery import ModuleSpec
from types import ModuleType

from sneks.engine.config.instantiation import config
from sneks.engine.interface.snek import Snek


@dataclass(frozen=True)
class Submission:
    name: str
    snek: Snek


def get_submissions() -> list[Submission]:
    sneks: list[Submission] = []
    snek_classes = get_submission_classes()
    for name, snek in snek_classes.items():
        if config.registrar_submission_sneks > 1:
            for i in range(config.registrar_submission_sneks):
                sneks.append(Submission(f"{name}{i}", snek()))  # type: ignore
        else:
            sneks.append(Submission(name, snek()))  # type: ignore
    return sneks


def get_submission_classes() -> dict[str, Snek]:
    results = {}
    submissions = set(
        p.parent
        for p in pathlib.Path(config.registrar_prefix).glob(f"**/submission.py")
    )
    for submission in submissions:
        name, snek = get_custom_snek(submission)
        if name is not None and snek is not None:
            results[name] = snek
    return results


def get_custom_snek(prefix: pathlib.Path) -> tuple[str | None, Snek | None]:
    name, module = load_module(prefix)
    if module is None:
        return None, None
    return name, module.CustomSnek


def load_module(prefix: pathlib.Path) -> tuple[str | None, ModuleType | None]:
    name, spec, module = get_module(prefix)
    if name is not None and spec is not None and module is not None:
        assert spec.loader is not None
        spec.loader.exec_module(module)
        sys.modules[name] = module
    return name, module


def get_module(
    prefix: pathlib.Path,
) -> tuple[str | None, ModuleSpec | None, ModuleType | None]:
    submission = get_submission(prefix)
    if submission is None:
        return None, None, None
    name = get_submission_name(submission)
    spec = importlib.util.spec_from_file_location(name, submission)
    module = importlib.util.module_from_spec(spec) if spec is not None else None
    return name, spec, module


def get_submission(prefix: pathlib.Path) -> pathlib.Path | None:
    files = get_submission_files(prefix)
    if files:
        return files[0]
    return None


def get_submission_files(prefix: pathlib.Path) -> list[pathlib.Path]:
    suffix = "submission.py"
    return list(prefix.glob(f"**/{suffix}"))


def get_submission_name(prefix: pathlib.Path) -> str:
    return str(prefix.relative_to(config.registrar_prefix).parent)
