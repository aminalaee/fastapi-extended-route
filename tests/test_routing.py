from starlette.applications import Starlette
from starlette.responses import PlainTextResponse
from starlette.testclient import TestClient

from fastapi_extended_route import Request, Route


def test_url_for() -> None:
    def index(request: Request) -> PlainTextResponse:
        url = request.url_for("index").add_query(a=1)
        return PlainTextResponse(str(url))

    app = Starlette(
        routes=[Route("/", index, name="index")],
    )

    client = TestClient(app=app)
    response = client.get("/")

    assert response.text == "http://testserver/?a=1"
