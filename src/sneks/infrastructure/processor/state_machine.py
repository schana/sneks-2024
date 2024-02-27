import aws_cdk
from aws_cdk import Duration
from aws_cdk import aws_iam as iam
from aws_cdk import aws_s3 as s3
from aws_cdk import aws_stepfunctions as step_functions
from aws_cdk import aws_stepfunctions_tasks as tasks
from constructs import Construct

from sneks.infrastructure.processor.lambdas import Lambdas


class StateMachine(Construct):
    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        distribution_id: str,
        submission_bucket: s3.Bucket,
        video_bucket: s3.Bucket,
        static_site_bucket: s3.Bucket,
        lambdas: Lambdas,
    ):
        super().__init__(scope=scope, id=construct_id)

        # Wait for the SQS dedupe time to get uploaded items in a "batch"
        task_wait = step_functions.Wait(
            self,
            "WaitForUploadComplete",
            time=step_functions.WaitTime.duration(Duration.minutes(5)),
        )

        # Move new files into "staging" folder before validation
        task_pre_process = tasks.LambdaInvoke(
            self,
            "PreProcessTask",
            lambda_function=lambdas.pre_processor,
            payload=step_functions.TaskInput.from_object(
                dict(bucket=submission_bucket.bucket_name)
            ),
            payload_response_only=True,
        )

        choice_post_pre_process = (
            step_functions.Choice(self, "PostPreProcessChoice")
            .when(
                step_functions.Condition.is_not_present("$.staged[0]"),
                step_functions.Succeed(self, "No new submissions"),
            )
            .afterwards(include_otherwise=True)
        )

        # Validate each staged submission using a map
        task_validate_map = step_functions.Map(
            self, "ValidateMap", items_path="$.staged"
        )
        task_validate = tasks.LambdaInvoke(
            self,
            "ValidateTask",
            lambda_function=lambdas.validator,
            payload_response_only=True,
        )
        # After validation, move submission to "submitted <timestamp>" or "invalid <timestamp>"
        task_post_validation = tasks.LambdaInvoke(
            self,
            "PostValidate",
            lambda_function=lambdas.post_validator,
            payload_response_only=True,
        )
        task_validate_map.iterator(
            task_validate.add_catch(task_post_validation, result_path="$.error").next(
                task_post_validation
            )
        )
        task_post_validate_reduce = tasks.LambdaInvoke(
            self,
            "PostValidateReduce",
            lambda_function=lambdas.post_validator_reduce,
            payload_response_only=True,
        )
        choice_post_validate = (
            step_functions.Choice(self, "PostValidateChoice")
            .when(
                step_functions.Condition.boolean_equals("$", False),
                step_functions.Succeed(self, "No new submissions validated"),
            )
            .afterwards(include_otherwise=True)
        )

        map_process_array = step_functions.Pass(
            self,
            "MapProcessArray",
            result=step_functions.Result(list(range(20))),
        )

        map_process = step_functions.Map(
            self,
            "MapProcess",
        )

        map_process.iterator(
            step_functions.Parallel(self, "ParallelProcess")
            .branch(
                tasks.LambdaInvoke(
                    self,
                    "ProcessTask",
                    lambda_function=lambdas.processor,
                    payload_response_only=True,
                    payload=step_functions.TaskInput.from_object(
                        dict(
                            submission_bucket=submission_bucket.bucket_name,
                        )
                    ),
                )
            )
            .branch(
                tasks.LambdaInvoke(
                    self,
                    "RecordTask",
                    lambda_function=lambdas.recorder,
                    payload_response_only=True,
                    payload=step_functions.TaskInput.from_object(
                        dict(
                            submission_bucket=submission_bucket.bucket_name,
                            video_bucket=video_bucket.bucket_name,
                        )
                    ),
                )
            )
            .next(
                tasks.LambdaInvoke(
                    self,
                    "PostProcessSaveTask",
                    lambda_function=lambdas.post_process_save,
                    payload_response_only=True,
                    payload=step_functions.TaskInput.from_object(
                        dict(
                            video_bucket=video_bucket.bucket_name,
                            static_site_bucket=static_site_bucket.bucket_name,
                            result=step_functions.JsonPath.object_at("$"),
                        )
                    ),
                )
            )
        )

        task_post_process = tasks.LambdaInvoke(
            self,
            "PostProcess",
            lambda_function=lambdas.post_processor,
            payload=step_functions.TaskInput.from_object(
                dict(
                    distribution_id=distribution_id,
                    static_site_bucket=static_site_bucket.bucket_name,
                    result=step_functions.JsonPath.object_at("$"),
                )
            ),
            payload_response_only=True,
        )

        task_cloudfront_invalidation = tasks.CallAwsService(
            self,
            "InvalidateManifest",
            service="cloudfront",
            action="createInvalidation",
            parameters={
                "DistributionId": distribution_id,
                "InvalidationBatch": {
                    "CallerReference.$": "$$.Execution.StartTime",
                    "Paths": {
                        "Items": ["/games/manifest.json"],
                        "Quantity": 1,
                    },
                },
            },
            iam_resources=[
                aws_cdk.Stack.of(self).format_arn(
                    service="cloudfront",
                    resource="distribution",
                    region="",
                    resource_name=distribution_id,
                )
            ],
            additional_iam_statements=[
                iam.PolicyStatement(
                    actions=["cloudfront:CreateInvalidation"],
                    resources=[
                        aws_cdk.Stack.of(self).format_arn(
                            service="cloudfront",
                            resource="distribution",
                            region="",
                            resource_name=distribution_id,
                        )
                    ],
                )
            ],
        )

        task_cloudfront_invalidation.add_retry(max_attempts=5)

        process_chain = (
            map_process_array.next(map_process)
            .next(task_post_process)
            .next(task_cloudfront_invalidation)
            .next(
                step_functions.Succeed(self, "Finished"),
            )
        )

        choice_manual_overrides = (
            step_functions.Choice(self, "ManualOverridesChoice")
            .when(
                step_functions.Condition.string_equals("$.goto", "process"),
                process_chain,
            )
            .when(
                step_functions.Condition.string_equals("$.goto", "pre-process"),
                step_functions.Pass(self, "SkipWait"),
            )
            .otherwise(task_wait)
        )

        definition = (
            choice_manual_overrides.afterwards()
            .next(task_pre_process)
            .next(choice_post_pre_process)
            .next(task_validate_map)
            .next(task_post_validate_reduce)
            .next(choice_post_validate)
            .next(process_chain)
        )

        self.workflow = step_functions.StateMachine(
            self, "Workflow", definition=definition, timeout=Duration.minutes(10)
        )
