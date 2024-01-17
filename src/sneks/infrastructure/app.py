import aws_cdk as cdk
from sneks2024.infrastructure.application.stack import Sneks2024
from sneks2024.infrastructure.pipeline.stack import PipelineStack


def main() -> None:
    app = cdk.App()
    Sneks2024(
        app,
        "sneks-2024",
        synthesizer=cdk.DefaultStackSynthesizer(
            generate_bootstrap_version_rule=False,
        ),
    )
    PipelineStack(app, "pipeline")
    app.synth()
