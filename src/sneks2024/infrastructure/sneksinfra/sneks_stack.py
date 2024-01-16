from collections import namedtuple

from aws_cdk import CfnOutput, Duration, RemovalPolicy, Stack
from aws_cdk import aws_events as events
from aws_cdk import aws_events_targets as targets
from aws_cdk import aws_iam as iam
from aws_cdk import aws_lambda as lambda_
from aws_cdk import aws_lambda_event_sources as lambda_event_sources
from aws_cdk import aws_s3 as s3
from aws_cdk import aws_sns as sns
from aws_cdk import aws_sqs as sqs
from aws_cdk import aws_stepfunctions as step_functions
from aws_cdk import aws_stepfunctions_tasks as tasks
from constructs import Construct
from sneksinfra.static_site import StaticSite

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


class SneksStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        submission_bucket, video_bucket, static_site_bucket = self.get_buckets()

        static_site = StaticSite(
            self,
            "StaticSite",
            submission_bucket=submission_bucket,
            static_site_bucket=static_site_bucket,
        )

        notification_topic = sns.Topic(
            self,
            "NotificationTopic",
        )

        sns.Subscription(
            self,
            "NotificationSubscription",
            topic=notification_topic,
            endpoint="admin@sneks.dev",
            protocol=sns.SubscriptionProtocol.EMAIL,
        )

        lambdas: Lambdas = self.get_lambdas(
            submission_bucket, video_bucket, static_site_bucket, notification_topic
        )

        iam.Grant.add_to_principal(
            scope=self,
            actions=["cloudfront:CreateInvalidation"],
            grantee=lambdas.post_processor,
            resource_arns=[
                self.format_arn(
                    service="cloudfront",
                    resource="distribution",
                    region="",
                    resource_name=static_site.distribution.distribution_id,
                )
            ],
        )

        self.build_submission_queue(submission_bucket, lambdas.start_processor)

        workflow = self.build_state_machine(
            distribution_id=static_site.distribution.distribution_id,
            submission_bucket=submission_bucket,
            video_bucket=video_bucket,
            static_site_bucket=static_site_bucket,
            lambdas=lambdas,
        )
        lambdas.start_processor.add_environment(
            "STATE_MACHINE_ARN", workflow.state_machine_arn
        )
        workflow.grant_start_execution(lambdas.start_processor)

        rule = events.Rule(
            self,
            "WorkflowStatusRule",
            enabled=True,
            event_pattern=events.EventPattern(
                source=["aws.states"],
                detail_type=["Step Functions Execution Status Change"],
                detail={"stateMachineArn": [workflow.state_machine_arn]},
            ),
        )

        rule.add_target(target=targets.LambdaFunction(handler=lambdas.notifier))

    def build_state_machine(
        self,
        distribution_id: str,
        submission_bucket: s3.Bucket,
        video_bucket: s3.Bucket,
        static_site_bucket: s3.Bucket,
        lambdas: Lambdas,
    ) -> step_functions.StateMachine:
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
                self.format_arn(
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
                        self.format_arn(
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

        return step_functions.StateMachine(
            self, "Workflow", definition=definition, timeout=Duration.minutes(10)
        )

    def get_buckets(self) -> (s3.Bucket, s3.Bucket, s3.Bucket):
        submission_bucket = s3.Bucket(
            self,
            "SubmissionBucket",
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
            enforce_ssl=True,
            cors=[
                s3.CorsRule(
                    allowed_headers=["*"],
                    allowed_methods=[s3.HttpMethods.PUT, s3.HttpMethods.GET],
                    allowed_origins=["*"],
                )
            ],
            event_bridge_enabled=True,
            transfer_acceleration=True,
        )

        video_bucket = s3.Bucket(
            self,
            "VideoBucket",
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
            enforce_ssl=True,
            removal_policy=RemovalPolicy.DESTROY,
            auto_delete_objects=True,
            lifecycle_rules=[
                s3.LifecycleRule(expiration=Duration.days(1)),
            ],
        )

        static_site_bucket = s3.Bucket(
            self,
            "StaticSiteBucket",
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
            enforce_ssl=True,
        )

        CfnOutput(
            self,
            "SneksSubmissionBucket",
            value=submission_bucket.bucket_name,
            export_name="SneksSubmissionBucket",
        )

        return submission_bucket, video_bucket, static_site_bucket

    def get_lambdas(
        self,
        submission_bucket: s3.Bucket,
        video_bucket: s3.Bucket,
        static_site_bucket: s3.Bucket,
        notification_topic: sns.Topic,
    ) -> Lambdas:
        notifier = self.build_python_lambda("Notifier", "send_notification")
        notifier.add_environment(
            key="sns_topic_arn", value=notification_topic.topic_arn
        )
        notification_topic.grant_publish(notifier)
        start_processor = self.build_python_lambda("StartProcessor", "start_processing")
        pre_processor = self.build_python_lambda(
            name="PreProcessor", handler="pre_process", timeout=Duration.seconds(20)
        )
        validator = self.build_python_lambda(
            name="Validator",
            handler="validate",
            timeout=Duration.seconds(60),
            use_pypy=True,
        )
        post_validator = self.build_python_lambda(
            name="PostValidator", handler="post_validate", timeout=Duration.seconds(20)
        )
        post_validator_reduce = self.build_python_lambda(
            name="PostValidatorReduce",
            handler="post_validate_reduce",
            timeout=Duration.seconds(20),
        )
        processor = self.build_python_lambda(
            name="Processor",
            handler="process",
            timeout=Duration.minutes(5),
            use_pypy=True,
        )
        recorder = self.build_python_lambda(
            name="Recorder",
            handler="record",
            timeout=Duration.minutes(4),
        )
        post_process_save = self.build_python_lambda(
            name="PostProcessSave",
            handler="post_process_save",
            timeout=Duration.seconds(20),
        )
        post_processor = self.build_python_lambda(
            name="PostProcessor", handler="post_process", timeout=Duration.seconds(30)
        )

        submission_bucket.grant_read_write(pre_processor)
        submission_bucket.grant_read(validator, objects_key_pattern="processing/*")
        submission_bucket.grant_read_write(post_validator)
        submission_bucket.grant_read(processor, objects_key_pattern="submitted/**/*.py")
        submission_bucket.grant_read(recorder, objects_key_pattern="submitted/**/*.py")
        video_bucket.grant_put(recorder, objects_key_pattern="games/*.mp4")
        video_bucket.grant_read(post_process_save, objects_key_pattern="games/*.mp4")
        static_site_bucket.grant_put(
            post_process_save, objects_key_pattern="games/*.mp4"
        )
        static_site_bucket.grant_read(
            post_process_save, objects_key_pattern="games/*.mp4"
        )
        static_site_bucket.grant_read_write(
            post_processor, objects_key_pattern="games/manifest*.json"
        )

        return Lambdas(
            notifier=notifier,
            start_processor=start_processor,
            pre_processor=pre_processor,
            validator=validator,
            post_validator=post_validator,
            post_validator_reduce=post_validator_reduce,
            processor=processor,
            recorder=recorder,
            post_process_save=post_process_save,
            post_processor=post_processor,
        )

    def build_python_lambda(
        self,
        name: str,
        handler: str,
        use_pypy: bool = False,
        timeout: Duration = Duration.seconds(3),
        memory_size: int = 1792,
    ):
        entrypoint = None
        if use_pypy:
            entrypoint = ["pypy", "-m", "awslambdaric"]

        return lambda_.DockerImageFunction(
            self,
            name,
            code=lambda_.DockerImageCode.from_image_asset(
                directory="app/processor",
                entrypoint=entrypoint,
                cmd=[f"main.{handler}"],
            ),
            timeout=timeout,
            memory_size=memory_size,
        )

    def build_submission_queue(
        self, submission_bucket: s3.Bucket, start_processor: lambda_.Function
    ) -> None:
        dead_letter_queue = sqs.Queue(
            self,
            "DeadLetterQueue",
            fifo=True,
            retention_period=Duration.days(14),
        )

        submission_queue = sqs.Queue(
            self,
            "SubmissionQueue",
            fifo=True,
            content_based_deduplication=True,
            dead_letter_queue=sqs.DeadLetterQueue(
                max_receive_count=3, queue=dead_letter_queue
            ),
        )

        rule = events.Rule(
            self,
            "SubmissionRule",
            enabled=True,
            event_pattern=events.EventPattern(
                source=["aws.s3"],
                detail_type=["Object Created"],
                resources=[submission_bucket.bucket_arn],
                detail={
                    "reason": ["PutObject"],
                    "object": {"key": [{"prefix": "private"}]},
                },
            ),
        )

        # Use SQS to provide deduplication so our downstream workflow only runs at most once every 5 minutes
        rule.add_target(
            target=targets.SqsQueue(
                queue=submission_queue,
                message=events.RuleTargetInput.from_event_path("$.detail.bucket.name"),
                message_group_id="submission",
            )
        )

        # Trigger the workflow from SQS by using a lambda
        submission_event = lambda_event_sources.SqsEventSource(
            queue=submission_queue,
            batch_size=1,
        )
        start_processor.add_event_source(submission_event)
