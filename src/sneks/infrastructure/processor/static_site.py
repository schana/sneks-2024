import aws_cdk
from aws_cdk import CfnOutput, Duration
from aws_cdk import aws_certificatemanager as certificate_manager
from aws_cdk import aws_cloudfront as cloudfront
from aws_cdk import aws_cloudfront_origins as cloudfront_origins
from aws_cdk import aws_cognito as cognito
from aws_cdk import aws_cognito_identitypool_alpha as cognito_identity
from aws_cdk import aws_s3 as s3
from aws_cdk import aws_s3_deployment as s3_deployment
from aws_cdk import aws_ssm as ssm
from constructs import Construct


class StaticSite(Construct):
    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        submission_bucket: s3.Bucket,
        static_site_bucket: s3.Bucket,
    ) -> None:
        super().__init__(scope, construct_id)

        self.distribution = cloudfront.Distribution(
            self,
            "Distribution",
            domain_names=["sneks.dev", "www.sneks.dev"],
            certificate=certificate_manager.Certificate.from_certificate_arn(
                self,
                "Certificate",
                ssm.StringParameter.value_for_string_parameter(self, "certificate-arn"),
            ),
            default_behavior=cloudfront.BehaviorOptions(
                origin=cloudfront_origins.S3Origin(
                    bucket=static_site_bucket,
                ),
                viewer_protocol_policy=cloudfront.ViewerProtocolPolicy.REDIRECT_TO_HTTPS,
            ),
            default_root_object="index.html",
            error_responses=[
                cloudfront.ErrorResponse(
                    http_status=403,
                    response_http_status=200,
                    response_page_path="/index.html",
                    ttl=Duration.millis(0),
                ),
            ],
            price_class=cloudfront.PriceClass.PRICE_CLASS_100,
        )

        s3_deployment.BucketDeployment(
            self,
            "StaticSiteDeployment",
            destination_bucket=static_site_bucket,
            sources=[s3_deployment.Source.asset("src/webapp/build")],
            retain_on_delete=False,
            distribution=self.distribution,
            exclude=["games/*", "aws-config.json"],
        )

        user_pool = cognito.UserPool(
            self,
            "UserPool",
            deletion_protection=True,
            self_sign_up_enabled=False,
            sign_in_aliases=cognito.SignInAliases(email=True),
            sign_in_case_sensitive=False,
            email=cognito.UserPoolEmail.with_cognito(
                reply_to="admin@sneks.dev",
            ),
            user_invitation=cognito.UserInvitationConfig(
                email_subject="Programming challenge invite",
                email_body=(
                    "<p>Dear {username},</p>"
                    "<p>Welcome to the Sneks programming challenge! "
                    "Visit the website at https://www.sneks.dev/start "
                    "to begin. You can get started by logging in with "
                    "your email and this temporary password:</p>"
                    "<code>{####}</code>"
                    "<p>Have fun and happy coding!</p>"
                ),
            ),
        )

        user_pool_client = user_pool.add_client(
            "Amplify",
            prevent_user_existence_errors=True,
            read_attributes=cognito.ClientAttributes().with_standard_attributes(
                email=True,
                email_verified=True,
            ),
        )

        identity_pool = cognito_identity.IdentityPool(
            self,
            "IdentityPool",
            authentication_providers=cognito_identity.IdentityPoolAuthenticationProviders(
                user_pools=[
                    cognito_identity.UserPoolAuthenticationProvider(
                        user_pool=user_pool,
                        user_pool_client=user_pool_client,
                        disable_server_side_token_check=False,
                    )
                ],
            ),
        )

        amplify_config = {
            "Auth": {
                "region": aws_cdk.Aws.REGION,
                "userPoolId": user_pool.user_pool_id,
                "userPoolWebClientId": user_pool_client.user_pool_client_id,
                "identityPoolId": identity_pool.identity_pool_id,
                "mandatorySignIn": True,
            },
            "Storage": {
                "AWSS3": {
                    "bucket": submission_bucket.bucket_name,
                    "region": aws_cdk.Aws.REGION,
                },
            },
        }

        s3_deployment.BucketDeployment(
            self,
            "amplify-config",
            destination_bucket=static_site_bucket,
            sources=[
                s3_deployment.Source.json_data(
                    object_key="aws-config.json",
                    obj=amplify_config,
                )
            ],
            retain_on_delete=False,
            distribution=self.distribution,
        )

        submission_bucket.grant_put(
            identity_pool.authenticated_role,
            objects_key_pattern="private/${cognito-identity.amazonaws.com:sub}/*.py",
        )
        submission_bucket.grant_put(
            identity_pool.authenticated_role,
            objects_key_pattern="private/${cognito-identity.amazonaws.com:sub}/*.pt",
        )
        submission_bucket.grant_put(
            identity_pool.authenticated_role,
            objects_key_pattern="private/${cognito-identity.amazonaws.com:sub}/*.pth",
        )
        submission_bucket.grant_read(
            identity_pool.authenticated_role,
            objects_key_pattern="private/${cognito-identity.amazonaws.com:sub}/*",
        )
        submission_bucket.grant_read(
            identity_pool.authenticated_role,
            objects_key_pattern="submitted/${cognito-identity.amazonaws.com:sub}/*",
        )
        submission_bucket.grant_read(
            identity_pool.authenticated_role,
            objects_key_pattern="invalid/${cognito-identity.amazonaws.com:sub}/*",
        )
        submission_bucket.grant_read(
            identity_pool.authenticated_role,
            objects_key_pattern="processing/${cognito-identity.amazonaws.com:sub}/*",
        )

        CfnOutput(
            self,
            "SneksCloudFrontDomain",
            value=self.distribution.distribution_domain_name,
            export_name="SneksCloudFrontDomain",
        )

        CfnOutput(
            self,
            "SneksCognitoUserPoolId",
            value=user_pool.user_pool_id,
            export_name="SneksCognitoUserPoolId",
        )

        CfnOutput(
            self,
            "SneksCognitoUserPoolClientId",
            value=user_pool_client.user_pool_client_id,
            export_name="SneksCognitoUserPoolClientId",
        )

        CfnOutput(
            self,
            "SneksCognitoIdentityPoolId",
            value=identity_pool.identity_pool_id,
            export_name="SneksCognitoIdentityPoolId",
        )
