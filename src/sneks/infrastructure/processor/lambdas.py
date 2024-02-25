import inspect
from typing import Any, Callable

import aws_cdk
from aws_cdk import aws_lambda as lambda_
from constructs import Construct


def get_handler(scope: Construct) -> lambda_.Function:
    source = lambda_.Code.from_asset("src", exclude=["tests/**", "webapp/**"])
    architecture = lambda_.Architecture.ARM_64
    runtime = lambda_.Runtime.PYTHON_3_12
    # Get the pre-packaged and optimized layer
    # https://docs.powertools.aws.dev/lambda/python/latest/#lambda-layer
    arch_specifier = "-Arm64" if architecture == lambda_.Architecture.ARM_64 else ""
    powertools_layer = lambda_.LayerVersion.from_layer_version_arn(
        scope,
        id="powertools-layer",
        layer_version_arn=(
            f"arn:aws:lambda:{aws_cdk.Aws.REGION}:017000801446:layer:AWSLambdaPowertoolsPythonV2"
            f"{arch_specifier}:58"
        ),
    )

    return lambda_.Function(
        scope,
        id="handler",
        architecture=architecture,
        runtime=runtime,
        layers=[powertools_layer],
        code=source,
        handler=get_handler_for_function(get_handler_for_function),
    )


def get_handler_for_function(function: Callable[[Any], Any]) -> str:
    module = inspect.getmodule(function)
    if module is None or module.__file__ is None:
        raise ValueError("module not found")

    return f"{module.__name__}.{function.__name__}"
