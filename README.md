# Opinionated FastAPI Extended Route

A small utility for FastAPI/Starlette Route and Request to address the following:

- `Request.url_for` doesn't allow adding `query parameters` at the moment.
- `URL` objects can't have multiple keys like `/?key=value&key=anothervalue`.

With the following changes:

- Make `Request.url_for` to match path parameters and use unmatched params for query parameters.
- Provide a custom `Route` which has a new `Request` type.
- Allow `URL` object to add multiple keys in `query params`.
- ...

Example:

```python
from fastapi import FastAPI
from fastapi.responses import PlainTextResponse

from fastapi_extended_route import Request, Route

def index(request: Request) -> PlainTextResponse:
    url = request.url_for("index", key=value)
    # url == "http://testserver/?key=value"
    return PlainTextResponse(url)

app = FastAPI(
    routes=[Route("/", index, name="index")],
)
```

As you can see the only change is to use `Route` from the package and
the new `Request` object will have a customized `url_for` method which
handles both path parameters and query parameters.

If/when these options are available in Starlette/FastAPI, this is no longer needed.
