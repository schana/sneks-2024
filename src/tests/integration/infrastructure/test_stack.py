import os

import boto3
from mypy_boto3_cloudformation import CloudFormationClient

from sneks.infrastructure.pipeline.stack import STACK_NAME_KEY


def test_stack_deployed() -> None:
    client: CloudFormationClient = boto3.client("cloudformation")
    assert client.describe_stacks(StackName=os.environ[STACK_NAME_KEY])["Stacks"][0]
