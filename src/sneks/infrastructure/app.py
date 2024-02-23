import aws_cdk as cdk

from sneks.infrastructure.pipeline.stack import PipelineStack
from sneks.infrastructure.processor.sneks_stack import SneksStack


def main() -> None:
    app = cdk.App()
    SneksStack(app, "sneks")
    PipelineStack(app, "pipeline")
    app.synth()
