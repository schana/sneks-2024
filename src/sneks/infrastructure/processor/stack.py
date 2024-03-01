import aws_cdk
from aws_cdk import CfnOutput, Duration, RemovalPolicy, Stack
from aws_cdk import aws_events as events
from aws_cdk import aws_events_targets as targets
from aws_cdk import aws_iam as iam
from aws_cdk import aws_lambda as lambda_
from aws_cdk import aws_lambda_event_sources as lambda_event_sources
from aws_cdk import aws_s3 as s3
from aws_cdk import aws_sns as sns
from aws_cdk import aws_sqs as sqs
from constructs import Construct

from sneks.application.backend import main
from sneks.infrastructure.processor.lambdas import (
    Lambdas,
    get_handler,
    get_handler_for_function,
)
from sneks.infrastructure.processor.state_machine import StateMachine
from sneks.infrastructure.processor.static_site import StaticSite


class Sneks(Stack):
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
        self.state_machine = StateMachine(
            self,
            construct_id="state_machine",
            distribution_id=static_site.distribution.distribution_id,
            submission_bucket=submission_bucket,
            video_bucket=video_bucket,
            static_site_bucket=static_site_bucket,
            lambdas=lambdas,
        )
        lambdas.start_processor.add_environment(
            "STATE_MACHINE_ARN", self.state_machine.workflow.state_machine_arn
        )
        self.state_machine.workflow.grant_start_execution(lambdas.start_processor)

        rule = events.Rule(
            self,
            "WorkflowStatusRule",
            enabled=True,
            event_pattern=events.EventPattern(
                source=["aws.states"],
                detail_type=["Step Functions Execution Status Change"],
                detail={
                    "stateMachineArn": [self.state_machine.workflow.state_machine_arn]
                },
            ),
        )

        rule.add_target(target=targets.LambdaFunction(handler=lambdas.notifier))

    def get_buckets(self) -> tuple[s3.Bucket, s3.Bucket, s3.Bucket]:
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
        layer = lambda_.LayerVersion(
            self,
            id="layer",
            code=lambda_.Code.from_asset(path="dist/layer"),
            removal_policy=aws_cdk.RemovalPolicy.DESTROY,
        )

        notifier = get_handler(
            self,
            name="Notifier",
            handler=get_handler_for_function(main.send_notification),
            layer=layer,
            environment={"sns_topic_arn": notification_topic.topic_arn},
        )
        start_processor = get_handler(
            self,
            name="StartProcessor",
            handler=get_handler_for_function(main.start_processing),
            layer=layer,
        )
        pre_processor = get_handler(
            self,
            name="PreProcessor",
            handler=get_handler_for_function(main.pre_process),
            layer=layer,
            timeout=Duration.seconds(20),
        )
        validator = get_handler(
            self,
            name="Validator",
            handler=get_handler_for_function(main.validate),
            layer=layer,
            timeout=Duration.seconds(60),
        )
        post_validator = get_handler(
            self,
            name="PostValidator",
            handler=get_handler_for_function(main.post_validate),
            layer=layer,
            timeout=Duration.seconds(20),
        )
        post_validator_reduce = get_handler(
            self,
            name="PostValidatorReduce",
            handler=get_handler_for_function(main.post_validate_reduce),
            layer=layer,
            timeout=Duration.seconds(20),
        )
        processor = get_handler(
            self,
            name="Processor",
            handler=get_handler_for_function(main.process),
            layer=layer,
            timeout=Duration.minutes(5),
        )
        recorder = get_handler(
            self,
            name="Recorder",
            handler=get_handler_for_function(main.record),
            layer=layer,
            timeout=Duration.minutes(4),
        )
        post_process_save = get_handler(
            self,
            name="PostProcessSave",
            handler=get_handler_for_function(main.post_process_save),
            layer=layer,
            timeout=Duration.seconds(20),
        )
        post_processor = get_handler(
            self,
            name="PostProcessor",
            handler=get_handler_for_function(main.post_process),
            layer=layer,
            timeout=Duration.seconds(30),
        )

        notification_topic.grant_publish(notifier)
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
