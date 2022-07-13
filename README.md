# FastAPI Extended Route

A small utility for FastAPI/Starlette Route and Request to address the following:

- `url_for` doesn't allow adding `query parameters` at the moment.
- `url_for` returns a `str` so it should be parseed to be modified.
- `URL` objects can't have multiple keys like `/?a=1&a=2`.

With the following changes:

- Provide a custom `Route` which has a new `Request` type.
- Make `Request.url_for` return an instance of `URL` instead of `str`.
- Allow `URL` object to add multiple keys in `query params`.
- ...

Example:

```python
from fastapi import FastAPI
from fastapi.responses import PlainTextResponse

from fastapi_extended_route import Request, Route

def index(request: Request) -> PlainTextResponse:
    url = request.url_for("index").add_query(a=1).add_query(a=2)
    # str(url) == "http://testserver/?a=1&a=2"
    return PlainTextResponse(str(url))

app = FastAPI(
    routes=[Route("/", index, name="index")],
)
```

If/when these options are available in Starlette/FastAPI, this is no longer needed.
