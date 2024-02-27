from sneks.infrastructure.processor.lambdas import get_handler_for_function


def test_cdk_app() -> None:
    import sneks.infrastructure.app

    sneks.infrastructure.app.main()


def test_get_handler_returns_path() -> None:
    assert (
        "sneks.infrastructure.processor.lambdas.get_handler_for_function"
        == get_handler_for_function(get_handler_for_function)
    )
