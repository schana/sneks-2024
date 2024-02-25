import aws_cdk as cdk

from sneks.infrastructure.pipeline.stack import Pipeline
from sneks.infrastructure.processor.stack import Sneks


def main() -> None:
    app = cdk.App()
    Sneks(app, "sneks")
    Pipeline(app, "pipeline")
    app.synth()
