from typing import Any, List

import aws_cdk as core
import aws_cdk.assertions as assertions

from sneks.application.api import router
from sneks.infrastructure.processor.stack import Sneks


def test_cdk_app() -> None:
    import sneks.infrastructure.app

    sneks.infrastructure.app.main()


def assert_resource_name_has_correct_type_and_props(
    stack: Sneks,
    template: assertions.Template,
    resources_list: List[str],
    cfn_type: str,
    props: Any,
) -> None:
    resources = template.find_resources(type=cfn_type, props=props)
    assert 1 == len(resources)
    assert get_logical_id(stack, resources_list) in resources


def get_logical_id(stack: Sneks, resources_list: List[str]) -> str:
    node = stack.node
    for resource in resources_list:
        node = node.find_child(resource).node
    cfnElement = node.default_child
    assert isinstance(cfnElement, core.CfnElement)
    return stack.get_logical_id(cfnElement)


def test_get_handler_returns_path(stack: Sneks) -> None:
    assert (
        "sneks.application.api.router.handle_request"
        == stack.get_handler_for_function(router.handle_request)
    )
