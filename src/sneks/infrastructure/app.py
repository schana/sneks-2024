import aws_cdk as cdk

from sneks.infrastructure.pipeline.stack import PipelineStack
from sneks.infrastructure.processor.stack import Sneks


def main() -> None:
    app = cdk.App()
    Sneks(app, "sneks")
    PipelineStack(app, "pipeline")
    app.synth()
