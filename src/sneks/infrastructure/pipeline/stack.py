import functools
import re
from typing import Any, Optional

import aws_cdk as cdk
from aws_cdk import Stack, Stage
from aws_cdk import aws_codebuild as codebuild
from aws_cdk import aws_codecommit as codecommit
from aws_cdk import aws_codepipeline as codepipeline
from aws_cdk import aws_iam as iam
from aws_cdk import aws_s3 as s3
from aws_cdk import pipelines
from constructs import Construct

from sneks.infrastructure.processor.stack import Sneks

RESOURCE_NAME_LENGTH_LIMIT = 30
STACK_NAME_KEY = "STACK_NAME"


class PipelineStack(Stack):
    """
    This stack establishes a pipeline that builds, deploys, and tests the app
    in a specified account. It uses a CodeCommit repo specified by context input
    to trigger the pipeline.

    The repo is configured using context parameters, specifically the following:

       - repository_name: CodeCommit repository name
       - branch: Branch to trigger the pipeline from
    """

    repository_name: str = "sneks-2024"
    branch: str = "main"

    def __init__(self, scope: Construct, construct_id: str) -> None:
        context_repo = scope.node.try_get_context("repository_name")
        if context_repo:
            self.repository_name = context_repo
        context_branch = scope.node.try_get_context("branch")
        if context_branch:
            self.branch = context_branch

        super().__init__(
            scope,
            construct_id,
            stack_name=self.get_resource_name(f"pipeline-stack"),
            description=f"Developer pipeline for {self.repository_name} repository on {self.branch} branch",
        )

        cache_bucket = s3.Bucket(
            self,
            "cache-bucket",
            enforce_ssl=True,
            removal_policy=cdk.RemovalPolicy.DESTROY,
            auto_delete_objects=True,
        )

        role = iam.Role(
            self,
            "pipeline-role",
            assumed_by=iam.ServicePrincipal("codepipeline.amazonaws.com"),
        )

        underlying_pipeline = codepipeline.Pipeline(
            self,
            "code-pipeline",
            pipeline_name=self.get_resource_name("pipeline"),
            role=role,
        )

        pipeline = pipelines.CodePipeline(
            self,
            "pipeline",
            code_pipeline=underlying_pipeline,
            synth=self.get_synth_step(cache_bucket),
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

        pipeline.add_wave("test", post=[self.get_integration_test_step(role)])

    def get_resource_name(self, name: str) -> str:
        """
        Returns a name with the repo and branch appended to differentiate pipelines between branches
        """
        concatenated = re.sub(r"[^a-zA-Z0-9-]+", "", f"{name}-{self.branch}")
        checksum = functools.reduce(
            lambda a, b: a ^ b,
            bytes(f"{self.repository_name}{self.branch}", "utf-8"),
        )
        return f"{concatenated[:RESOURCE_NAME_LENGTH_LIMIT - 2]}{checksum:02x}"

    def get_connection(self) -> pipelines.CodePipelineSource:
        return pipelines.CodePipelineSource.code_commit(
            repository=codecommit.Repository.from_repository_name(
                scope=self,
                id="codecommit-source",
                repository_name=self.repository_name,
            ),
            branch=self.branch,
        )

    def get_synth_step(self, cache_bucket: s3.IBucket) -> pipelines.CodeBuildStep:
        return pipelines.CodeBuildStep(
            "synth",
            input=self.get_connection(),
            env=dict(
                REPOSITORY_NAME=self.repository_name,
                BRANCH=self.branch,
            ),
            install_commands=[
                "pip install tox",
            ],
            commands=[
                "tox --recreate --parallel-no-spinner -- --junitxml=pytest-report.xml",
                "tox -e synth -- -c repository_name=$REPOSITORY_NAME -c branch=$BRANCH",
            ],
            partial_build_spec=self.get_partial_build_spec(
                dict(
                    reports=self.get_reports_build_spec_mapping("pytest-report.xml"),
                    cache=dict(
                        paths=[
                            ".mypy_cache/**/*",
                            ".tox/**/*",
                            "/root/.cache/pip/**/*",
                        ]
                    ),
                    phases=self.get_python_version_build_spec_mapping(),
                )
            ),
            cache=codebuild.Cache.bucket(cache_bucket),
        )

    def get_integration_test_step(self, role: iam.Role) -> pipelines.CodeBuildStep:
        stack_name = self.deploy_stage.stack_name
        return pipelines.CodeBuildStep(
            "integration-test",
            install_commands=[
                "pip install tox",
            ],
            env={STACK_NAME_KEY: stack_name},
            commands=["tox -e integration -- --junitxml=pytest-integration-report.xml"],
            role_policy_statements=[
                iam.PolicyStatement(
                    effect=iam.Effect.ALLOW,
                    actions=["sts:AssumeRole"],
                    resources=[role.role_arn],
                ),
                iam.PolicyStatement(
                    effect=iam.Effect.ALLOW,
                    actions=[
                        "cloudformation:DescribeStacks",
                    ],
                    resources=[
                        cdk.Stack.of(self).format_arn(
                            resource="stack",
                            service="cloudformation",
                            resource_name=f"{stack_name[:25]}*",
                        )
                    ],
                ),
            ],
            partial_build_spec=self.get_partial_build_spec(
                dict(
                    reports=self.get_reports_build_spec_mapping(
                        "pytest-integration-report.xml"
                    ),
                    phases=self.get_python_version_build_spec_mapping(),
                )
            ),
        )

    def get_partial_build_spec(self, mapping: dict[str, Any]) -> codebuild.BuildSpec:
        return codebuild.BuildSpec.from_object(mapping)

    def get_reports_build_spec_mapping(self, filename: str) -> dict[str, Any]:
        return {
            "pytest_reports": {
                "files": [filename],
                "file-format": "JUNITXML",
            }
        }

    def get_python_version_build_spec_mapping(self) -> dict[str, Any]:
        return {"install": {"runtime-versions": {"python": "3.12"}}}


class DeployStage(Stage):
    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        env: Optional[cdk.Environment] = None,
    ) -> None:
        super().__init__(scope, construct_id, env=env)
        stack = Sneks(self, "sneks")
        self.stack_name = stack.stack_name
