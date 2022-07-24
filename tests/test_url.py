from starlette.datastructures import MultiDict

from fastapi_extended_route import URL


def test_include_query_params() -> None:
    url = URL("http://testserver/")
    url = url.include_query_params(key="value")

    assert str(url) == "http://testserver/?key=value"


def test_replace_query_params() -> None:
    url = URL("http://testserver/?key=value")
    url = url.replace_query_params(key="value")

    assert str(url) == "http://testserver/?key=value"


def test_include_query_params_multiple() -> None:
    params = MultiDict()
    params.append("key", "value")
    params.append("key", "value")
    url = URL("http://testserver/")
    url = url.include_query_params(params)

    assert str(url) == "http://testserver/?key=value&key=value"
