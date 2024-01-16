from typing import Any

from aws_lambda_powertools import Logger, Tracer
from aws_lambda_powertools.event_handler import APIGatewayRestResolver
from aws_lambda_powertools.logging import correlation_paths
from aws_lambda_powertools.utilities.typing import LambdaContext
from pydantic import BaseModel

logger = Logger()
tracer = Tracer()
app = APIGatewayRestResolver(enable_validation=True)


class Response(BaseModel):
    hello: str


@app.get("/hello/<name>")  # type: ignore
@tracer.capture_method
def get_hello(name: str) -> Response:
    return Response(hello=name)


@logger.inject_lambda_context(correlation_id_path=correlation_paths.API_GATEWAY_REST)
@tracer.capture_lambda_handler
def handle_request(event: dict[str, Any], context: LambdaContext) -> dict[str, Any]:
    return app.resolve(event, context)
