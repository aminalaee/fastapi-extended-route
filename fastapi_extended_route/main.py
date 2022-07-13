import asyncio
import functools
import inspect
from typing import Any, Callable, List, Optional
from urllib.parse import parse_qsl, urlencode

from starlette.concurrency import run_in_threadpool
from starlette.datastructures import URL as _URL
from starlette.datastructures import MultiDict
from starlette.requests import Request as _Request
from starlette.routing import Route as _Route
from starlette.routing import Router, compile_path, get_name
from starlette.types import ASGIApp, Receive, Scope, Send


def is_async_callable(obj: Any) -> bool:
    while isinstance(obj, functools.partial):
        obj = obj.func

    return asyncio.iscoroutinefunction(obj) or (
        callable(obj) and asyncio.iscoroutinefunction(obj.__call__)
    )


class URL(_URL):
    def add_query(self, **kwargs: Any) -> "URL":
        params = MultiDict(parse_qsl(self.query, keep_blank_values=True))
        for key, value in kwargs.items():
            params.append(str(key), str(value))
        query = urlencode(params.multi_items())
        return self.replace(query=query)

    def replace_query(self, **kwargs: Any) -> "URL":
        params = MultiDict(parse_qsl(self.query, keep_blank_values=True))
        params.update({str(key): str(value) for key, value in kwargs.items()})
        query = urlencode(params.multi_items())
        return self.replace(query=query)

    def include_query_params(self, **kwargs: Any) -> "URL":
        return self.add_query(**kwargs)

    def replace_query_params(self, **kwargs: Any) -> "URL":
        return self.replace_query(**kwargs)


class Request(_Request):
    def url_for(self, name: str, **path_params: Any) -> URL:
        router: Router = self.scope["router"]
        url_path = router.url_path_for(name, **path_params)
        return URL(url_path.make_absolute_url(base_url=self.base_url))


def request_response(func: Callable) -> ASGIApp:
    """
    Takes a function or coroutine `func(request) -> response`,
    and returns an ASGI application.
    """
    is_coroutine = is_async_callable(func)

    async def app(scope: Scope, receive: Receive, send: Send) -> None:
        request = Request(scope, receive=receive, send=send)
        if is_coroutine:
            response = await func(request)
        else:
            response = await run_in_threadpool(func, request)
        await response(scope, receive, send)

    return app


class Route(_Route):
    def __init__(
        self,
        path: str,
        endpoint: Callable,
        *,
        methods: Optional[List[str]] = None,
        name: Optional[str] = None,
        include_in_schema: bool = True,
    ) -> None:
        assert path.startswith("/"), "Routed paths must start with '/'"
        self.path = path
        self.endpoint = endpoint
        self.name = get_name(endpoint) if name is None else name
        self.include_in_schema = include_in_schema

        endpoint_handler = endpoint
        while isinstance(endpoint_handler, functools.partial):
            endpoint_handler = endpoint_handler.func
        if inspect.isfunction(endpoint_handler) or inspect.ismethod(endpoint_handler):
            # Endpoint is function or method. Treat it as `func(request) -> response`.
            self.app = request_response(endpoint)
            if methods is None:
                methods = ["GET"]
        else:
            # Endpoint is a class. Treat it as ASGI.
            self.app = endpoint

        if methods is None:
            self.methods = None
        else:
            self.methods = {method.upper() for method in methods}
            if "GET" in self.methods:
                self.methods.add("HEAD")

        self.path_regex, self.path_format, self.param_convertors = compile_path(path)
