import aws_cdk as core
import aws_cdk.assertions as assertions
import pytest

from sneks2024.infrastructure.application.stack import Sneks2024


@pytest.fixture
def app() -> core.App:
    app = core.App(
        context={
            "@aws-cdk/aws-iam:minimizePolicies": True,
        }
    )
    return app


@pytest.fixture
def stack(app: core.App) -> Sneks2024:
    stack = Sneks2024(app, "sneks")
    return stack


@pytest.fixture
def template(stack: Sneks2024) -> assertions.Template:
    return assertions.Template.from_stack(stack)
