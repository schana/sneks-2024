import pathlib

import sneks.submission.scripts.config as script_config
from sneks import submission
from sneks.engine.config.instantiation import config as sneks_config
from sneks.engine.engine import runner
from sneks.engine.validator import main as validator

prefix = str(pathlib.Path(submission.__file__).resolve().parent)


def validate():
    validator.main(test_path=prefix)


def run():
    sneks_config.registrar_prefix = prefix
    sneks_config.graphics.step_delay = script_config.STEP_DELAY_MILLISECONDS
    sneks_config.graphics.step_keypress_wait = (
        script_config.STEP_DELAY_WAIT_FOR_KEYPRESS
    )
    sneks_config.graphics.end_delay = script_config.END_DELAY_MILLISECONDS
    sneks_config.graphics.end_keypress_wait = script_config.END_DELAY_WAIT_FOR_KEYPRESS
    runner.main()
