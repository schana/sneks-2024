import inspect
from collections import namedtuple
from typing import Any, Callable

import aws_cdk
from aws_cdk import aws_lambda as lambda_
from constructs import Construct

Lambdas = namedtuple(
    "Lambdas",
    [
        "notifier",
        "start_processor",
        "pre_processor",
        "validator",
        "post_validator",
        "post_validator_reduce",
        "processor",
        "recorder",
        "post_process_save",
        "post_processor",
    ],
)


def get_handler(
    scope: Construct,
    name: str,
    handler: str,
    timeout: aws_cdk.Duration = aws_cdk.Duration.seconds(3),
    memory_size: int = 1792,
    environment: dict[str, str] | None = None,
) -> lambda_.Function:
    source = lambda_.Code.from_asset("src", exclude=["tests/**", "webapp/**"])
    architecture = lambda_.Architecture.ARM_64
    runtime = lambda_.Runtime.PYTHON_3_12

    return lambda_.Function(
        scope,
        id=name,
        runtime=runtime,
        architecture=architecture,
        timeout=timeout,
        memory_size=memory_size,
        layers=[],
        environment=environment,
        code=source,
        handler=handler,
    )


def get_handler_for_function(function: Callable[..., Any]) -> str:
    module = inspect.getmodule(function)
    if module is None or module.__file__ is None:
        raise ValueError("module not found")

    return f"{module.__name__}.{function.__name__}"
