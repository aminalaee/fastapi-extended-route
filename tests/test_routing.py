import pytest
from starlette.responses import PlainTextResponse
from starlette.routing import NoMatchFound, Router

from fastapi_extended_route import Request, Route


def test_router(test_client_factory) -> None:
    def home(request: Request) -> PlainTextResponse:
        return PlainTextResponse(str(request.url))

    def profile(request: Request) -> PlainTextResponse:
        return PlainTextResponse(str(request.url))

    router = Router(
        routes=[
            Route("/", home, name="home"),
            Route("/profile/{username}", profile, name="profile"),
        ],
    )

    client = test_client_factory(router)

    response = client.get("/")
    assert response.text == "http://testserver/"

    response = client.get("/profile/amin")
    assert response.text == "http://testserver/profile/amin"


def test_url_for(test_client_factory):
    def home(request: Request) -> PlainTextResponse:
        return PlainTextResponse(str(request.url_for("home")))

    def profile(request: Request) -> PlainTextResponse:
        return PlainTextResponse(str(request.url_for("profile", username="amin")))

    router = Router(
        routes=[
            Route("/", home, name="home"),
            Route("/profile/{username}", profile, name="profile"),
        ],
    )
    client = test_client_factory(router)

    response = client.get("/")
    assert response.text == "http://testserver/"

    response = client.get("/profile/amin")
    assert response.text == "http://testserver/profile/amin"


def test_url_for_query_params(test_client_factory):
    def home(request: Request) -> PlainTextResponse:
        return PlainTextResponse(str(request.url_for("home", key="value")))

    def profile(request: Request) -> PlainTextResponse:
        return PlainTextResponse(
            str(request.url_for("profile", username="amin", key="value"))
        )

    def extra(request: Request) -> PlainTextResponse:
        return PlainTextResponse(str(request.url_for("profile", key="value")))

    router = Router(
        routes=[
            Route("/", home, name="home"),
            Route("/profile/{username}", profile, name="profile"),
            Route("/extra", extra, name="extra"),
        ],
    )

    client = test_client_factory(router)

    response = client.get("/")
    assert response.text == "http://testserver/?key=value"

    response = client.get("/profile/amin")
    assert response.text == "http://testserver/profile/amin?key=value"

    with pytest.raises(NoMatchFound):
        client.get("/extra")
