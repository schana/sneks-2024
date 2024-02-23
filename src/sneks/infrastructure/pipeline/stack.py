import functools
import re
from typing import Optional

import aws_cdk as cdk
from aws_cdk import Stack, Stage
from aws_cdk import aws_codebuild as codebuild
from aws_cdk import pipelines
from constructs import Construct

from sneks.infrastructure.pipeline.source import CodeStarSource
from sneks.infrastructure.processor.sneks_stack import SneksStack

RESOURCE_NAME_LENGTH_LIMIT = 30
STACK_NAME_KEY = "STACK_NAME"


class PipelineStack(Stack):
    """
    This stack establishes a pipeline that builds, deploys, and tests the app
    in a specified account. It uses CodeStar connections to set up a webhook
    to GitHub specified by context input to trigger the pipeline for commits.

    The repo is configured using context parameters, specifically the following:

       - owner: repo owner
       - repo: repository name
       - branch: branch to trigger the pipeline from
       - arn: CodeStar Connection ARN

    Set up the connection by following the documentation at
    https://docs.aws.amazon.com/dtconsole/latest/userguide/connections-create-github.html
    """

    owner: str = "schana"
    repo: str = "sneks-2024"
    branch: str = "main"
    arn: str = ""

    def __init__(self, scope: Construct, construct_id: str) -> None:
        context_owner = scope.node.try_get_context("owner")
        if context_owner:
            self.owner = context_owner
        context_repo = scope.node.try_get_context("repo")
        if context_repo:
            self.repo = context_repo
        context_branch = scope.node.try_get_context("branch")
        if context_branch:
            self.branch = context_branch
        context_arn = scope.node.try_get_context("arn")
        if context_arn:
            self.arn = context_arn

        super().__init__(
            scope,
            construct_id,
            stack_name=self.get_resource_name(f"pipeline-stack"),
            description=f"Pipeline for {self.repo} repository on {self.branch} branch",
        )

        pipeline = pipelines.CodePipeline(
            self,
            "pipeline",
            synth=self.get_synth_step(),
            code_build_defaults=pipelines.CodeBuildOptions(
                build_environment=codebuild.BuildEnvironment(
                    build_image=codebuild.LinuxBuildImage.STANDARD_7_0,
                    compute_type=codebuild.ComputeType.SMALL,
                )
            ),
        )

        self.deploy_stage = DeployStage(
            self,
            self.get_resource_name("deploy"),
        )
        pipeline.add_stage(self.deploy_stage)

    def get_resource_name(self, name: str) -> str:
        """
        Returns a name with the repo and branch appended to differentiate pipelines between branches
        """
        concatenated = re.sub(r"[^a-zA-Z0-9-]+", "", f"{name}-{self.branch}")
        checksum = functools.reduce(
            lambda a, b: a ^ b,
            bytes(f"{self.repo}{self.branch}", "utf-8"),
        )
        return f"{concatenated[:RESOURCE_NAME_LENGTH_LIMIT - 2]}{checksum:02x}"

    def get_connection(self) -> CodeStarSource:
        return CodeStarSource(
            name="code-star-connection",
            connection_arn=self.arn,
            owner=self.owner,
            repo=self.repo,
            branch=self.branch,
        )

    def get_synth_step(self) -> pipelines.CodeBuildStep:
        return pipelines.CodeBuildStep(
            "synth",
            input=self.get_connection(),
            env=dict(
                OWNER=self.owner,
                REPO=self.repo,
                BRANCH=self.branch,
                ARN=self.arn,
            ),
            install_commands=[
                "pip install tox",
            ],
            commands=[
                "tox --parallel-no-spinner",
                "tox -e synth -- -c owner=$OWNER -c repo=$REPO -c branch=$BRANCH -c arn=$ARN",
            ],
            partial_build_spec=codebuild.BuildSpec.from_object(
                {"phases": {"install": {"runtime-versions": {"python": "3.12"}}}}
            ),
        )


class DeployStage(Stage):
    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        env: Optional[cdk.Environment] = None,
    ) -> None:
        super().__init__(scope, construct_id, env=env)
        stack = SneksStack(self, "sneks")
        self.stack_name = stack.stack_name
