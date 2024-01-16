import importlib
import importlib.util
import pathlib
import sys
from dataclasses import dataclass
from importlib.machinery import ModuleSpec
from types import ModuleType
from typing import Dict, List, Optional

from sneks.config.config import config
from sneks.interface.snek import Snek


@dataclass(frozen=True)
class Submission:
    name: str
    snek: Snek


def get_submissions() -> List[Submission]:
    sneks: List[Submission] = []
    snek_classes = get_submission_classes()
    for name, snek in snek_classes.items():
        if config.registrar_submission_sneks > 1:
            for i in range(config.registrar_submission_sneks):
                sneks.append(Submission(f"{name}{i}", snek()))
        else:
            sneks.append(Submission(name, snek()))
    return sneks


def get_submission_classes() -> Dict[str, Snek.__class__]:
    results = {}
    submissions = set(
        p.parent
        for p in pathlib.Path(config.registrar_prefix).glob(f"**/submission.py")
    )
    for submission in submissions:
        name, snek = get_custom_snek(submission)
        if snek is not None:
            results[name] = snek
    return results


def get_custom_snek(prefix: pathlib.Path) -> (Optional[str], Optional[Snek]):
    name, module = load_module(prefix)
    if module is None:
        return None, None
    return name, module.CustomSnek


def load_module(prefix: pathlib.Path) -> (Optional[str], Optional[ModuleType]):
    name, spec, module = get_module(prefix)
    if module is not None:
        spec.loader.exec_module(module)
        sys.modules[name] = module
    return name, module


def get_module(
    prefix: pathlib.Path,
) -> (Optional[str], Optional[ModuleSpec], Optional[ModuleType]):
    submission = get_submission(prefix)
    if submission is None:
        return None, None, None
    name = get_submission_name(submission)
    spec = importlib.util.spec_from_file_location(name, submission)
    module = importlib.util.module_from_spec(spec)
    return name, spec, module


def get_submission(prefix: pathlib.Path) -> Optional[pathlib.Path]:
    files = get_submission_files(prefix)
    if files:
        return files[0]
    return None


def get_submission_files(prefix: pathlib.Path) -> List[pathlib.Path]:
    suffix = "submission.py"
    return list(prefix.glob(f"**/{suffix}"))


def get_submission_name(prefix: pathlib.Path) -> str:
    return str(prefix.relative_to(config.registrar_prefix).parent)
