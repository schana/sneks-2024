import functools
import re
from typing import Optional

import aws_cdk
import aws_cdk as cdk
from aws_cdk import Stack, Stage, aws_s3, pipelines
from aws_cdk import aws_codebuild as codebuild
from constructs import Construct

from sneks.infrastructure.pipeline.source import CodeStarSource
from sneks.infrastructure.processor.stack import Sneks

RESOURCE_NAME_LENGTH_LIMIT = 30


class Pipeline(Stack):
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
            stack_name=self.get_resource_name("pipeline-stack"),
            description=f"Pipeline for {self.repo} repository on {self.branch} branch",
        )

        cache_bucket = aws_s3.Bucket(
            self,
            "cache",
            removal_policy=aws_cdk.RemovalPolicy.DESTROY,
            auto_delete_objects=True,
            lifecycle_rules=[
                aws_s3.LifecycleRule(
                    enabled=True,
                    expiration=aws_cdk.Duration.days(10),
                )
            ],
        )

        pipeline = pipelines.CodePipeline(
            self,
            "pipeline",
            synth=self.get_synth_step(cache_bucket),
            code_build_defaults=pipelines.CodeBuildOptions(
                build_environment=codebuild.BuildEnvironment(
                    build_image=codebuild.LinuxBuildImage.STANDARD_7_0,
                    compute_type=codebuild.ComputeType.SMALL,
                )
            ),
            docker_enabled_for_synth=True,
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

    @functools.cached_property
    def connection(self) -> CodeStarSource:
        return CodeStarSource(
            name="code-star-connection",
            connection_arn=self.arn,
            owner=self.owner,
            repo=self.repo,
            branch=self.branch,
        )

    def get_synth_step(self, cache_bucket: aws_s3.Bucket) -> pipelines.CodeBuildStep:
        return pipelines.CodeBuildStep(
            "synth",
            input=self.connection,
            env=dict(
                OWNER=self.owner,
                REPO=self.repo,
                BRANCH=self.branch,
                ARN=self.arn,
                priviledged="true",
            ),
            cache=codebuild.Cache.bucket(cache_bucket),
            build_environment=codebuild.BuildEnvironment(
                build_image=codebuild.LinuxBuildImage.STANDARD_7_0,
                compute_type=codebuild.ComputeType.SMALL,
            ),
            install_commands=[
                "pip install tox",
                "docker run --privileged --rm public.ecr.aws/eks-distro-build-tooling/binfmt-misc:qemu-v7.0.0 --install arm64",
            ],
            commands=[
                "tox --parallel-no-spinner -m build",
                "tox -e synth -- -c owner=$OWNER -c repo=$REPO -c branch=$BRANCH -c arn=$ARN",
            ],
            partial_build_spec=codebuild.BuildSpec.from_object(
                {
                    "phases": {
                        "install": {
                            "runtime-versions": {"python": "3.12", "nodejs": "20"}
                        }
                    },
                    "cache": {
                        "paths": ["/root/.cache/**/*"],
                    },
                }
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
        Sneks(self, "sneks")
