from fastapi_extended_route import URL


def test_add_query() -> None:
    url = URL("http://testserver/")
    url = url.add_query(a=1)

    assert str(url) == "http://testserver/?a=1"


def test_include_query_params() -> None:
    url = URL("http://testserver/")
    url = url.include_query_params(a=1)

    assert str(url) == "http://testserver/?a=1"


def test_replace_query() -> None:
    url = URL("http://testserver/?a=1")
    url = url.replace_query(a=10)

    assert str(url) == "http://testserver/?a=10"


def test_replace_query_params() -> None:
    url = URL("http://testserver/?a=1")
    url = url.replace_query_params(a=10)

    assert str(url) == "http://testserver/?a=10"


def test_multiple_add_query() -> None:
    url = URL("http://testserver/")
    url = url.add_query(a=10)
    url = url.add_query(a=20)

    assert str(url) == "http://testserver/?a=10&a=20"
