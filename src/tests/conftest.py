import aws_cdk as core
import aws_cdk.assertions as assertions
import pytest

from sneks.infrastructure.processor.stack import Sneks


@pytest.fixture
def app() -> core.App:
    app = core.App(
        context={
            "@aws-cdk/aws-iam:minimizePolicies": True,
        }
    )
    return app


@pytest.fixture
def stack(app: core.App) -> Sneks:
    stack = Sneks(app, "sneks")
    return stack


@pytest.fixture
def template(stack: Sneks) -> assertions.Template:
    return assertions.Template.from_stack(stack)
