import asyncio
import functools
import inspect
from typing import Any, Callable, Dict, List, Optional, Tuple, Union
from urllib.parse import parse_qsl, urlencode

from starlette.concurrency import run_in_threadpool
from starlette.convertors import Convertor
from starlette.datastructures import (
    URL as _URL,
    ImmutableMultiDict,
    MultiDict,
    URLPath as _URLPath,
)
from starlette.requests import Request as _Request
from starlette.routing import (
    NoMatchFound,
    Route as _Route,
    Router,
    compile_path,
    get_name,
)
from starlette.types import ASGIApp, Receive, Scope, Send


def is_async_callable(obj: Any) -> bool:
    while isinstance(obj, functools.partial):
        obj = obj.func

    return asyncio.iscoroutinefunction(obj) or (
        callable(obj) and asyncio.iscoroutinefunction(obj.__call__)
    )


def replace_params(
    path: str,
    param_convertors: Dict[str, Convertor],
    params: Dict[str, str],
) -> Tuple[str, dict]:
    for key, value in list(params.items()):
        if "{" + key + "}" in path:
            convertor = param_convertors[key]
            value = convertor.to_string(value)
            path = path.replace("{" + key + "}", value)
            params.pop(key)
    return path, params


class URL(_URL):
    def include_query_params(
        self, __params: Optional[ImmutableMultiDict[str, str]] = None, **kwargs: Any
    ) -> str:
        params = MultiDict(parse_qsl(self.query, keep_blank_values=True))

        if __params:
            for key, value in __params.multi_items():
                params.append(str(key), str(value))

        for key, value in kwargs.items():
            params.append(str(key), str(value))
        query = urlencode(params.multi_items())
        return str(self.replace(query=query))


class URLPath(_URLPath):
    def __new__(
        cls,
        path: str,
        protocol: str = "",
        host: str = "",
        query_params: Dict[str, Any] = None,
    ) -> "URLPath":
        assert protocol in ("http", "websocket", "")
        return str.__new__(cls, path)

    def __init__(
        self,
        path: str,
        protocol: str = "",
        host: str = "",
        query_params: Dict[str, Any] = None,
    ) -> None:
        self.query_params = query_params or {}
        super().__init__(path, protocol, host)

    def make_absolute_url(self, base_url: Union[str, URL]) -> str:
        if isinstance(base_url, str):
            base_url = URL(base_url)
        if self.protocol:
            scheme = {
                "http": {True: "https", False: "http"},
                "websocket": {True: "wss", False: "ws"},
            }[self.protocol][base_url.is_secure]
        else:
            scheme = base_url.scheme

        netloc = self.host or base_url.netloc
        path = base_url.path.rstrip("/") + str(self)
        url = URL(scheme=scheme, netloc=netloc, path=path)
        return str(url.include_query_params(**self.query_params))


class Request(_Request):
    def url_for(self, name: str, **params: Any) -> URL:
        """
        Takes a `name` and keyword arguments and will first try to
        match them with path parameters, any unused keywords will
        be treated as query parameters in the URL.
        """
        router: Router = self.scope["router"]
        url_path = router.url_path_for(name, **params)
        return url_path.make_absolute_url(base_url=self.base_url)


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

    def url_path_for(self, name: str, **params: Any) -> URLPath:
        seen_params = set(params.keys())
        expected_params = set(self.param_convertors.keys())

        if name != self.name or len(expected_params - seen_params) > 0:
            raise NoMatchFound(name, {})

        path, remaining_params = replace_params(
            self.path_format, self.param_convertors, params
        )
        return URLPath(path=path, protocol="http", query_params=remaining_params)
