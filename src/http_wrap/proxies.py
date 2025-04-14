from collections.abc import Mapping
from datetime import timedelta
from http import HTTPStatus
from types import MethodType, TracebackType
from typing import Any, Callable, Optional, Sequence, Tuple, Type, Union

import wrapt

from http_wrap.configs import RedactHeaders
from http_wrap.hooks import extract_host, sanitize_headers
from http_wrap.interfaces import (
    ALLOWED_METHODS,
    HTTPWrapClient,
    HTTPWrapResponse,
    WrapResponse,
    WrapURL,
    httpmethod,
)


class ResponseProxy(wrapt.ObjectProxy):
    def __init__(self, response: Any, redact: Optional[RedactHeaders] = None) -> None:
        super().__init__(response)
        if not hasattr(self, "status_code"):
            self.status_code = getattr(response, "status", 0)

        if not hasattr(self, "status") and hasattr(self, "status_code"):
            self.status = self.status_code

        status = HTTPStatus(self.status_code)

        if not hasattr(self, "reason"):
            self.reason = status.phrase

        if not hasattr(self, "reason_phrase"):
            self.reason_phrase = status.phrase.upper()

        if not hasattr(self, "ok"):
            self.ok = status.is_success or status.is_redirection

        if not hasattr(self, "is_informational"):
            self.is_informational = status.is_informational

        if not hasattr(self, "is_success"):
            self.is_success = status.is_success

        if not hasattr(self, "is_redirect"):
            self.is_redirect = status.is_redirection

        if not hasattr(self, "is_client_error"):
            self.is_client_error = status.is_client_error

        if not hasattr(self, "is_server_error"):
            self.is_server_error = status.is_server_error

        if not hasattr(self, "is_error"):
            self.is_error = status.is_client_error or status.is_server_error

        if not hasattr(self, "is_permanent_redirect"):
            self.is_permanent_redirect = (
                "location" in response.headers
                and self.status_code
                in (HTTPStatus.MOVED_PERMANENTLY, HTTPStatus.PERMANENT_REDIRECT)
            )

        if not hasattr(self, "has_redirect_location"):
            self.has_redirect_location = (
                "location" in response.headers
                and self.status_code
                in {
                    HTTPStatus.MOVED_PERMANENTLY,
                    HTTPStatus.FOUND,
                    HTTPStatus.SEE_OTHER,
                    HTTPStatus.TEMPORARY_REDIRECT,
                    HTTPStatus.PERMANENT_REDIRECT,
                }
            )

        if hasattr(response, "raise_for_status"):

            original_raise = response.raise_for_status

            def raise_for_status_sync(resp: Any) -> Any:
                original_raise()
                return resp

            self.raise_for_status = MethodType(raise_for_status_sync, self)

        if hasattr(response, "headers") and not hasattr(self, "raw_headers"):
            try:
                self.raw_headers = [
                    (k.lower().encode("utf-8"), v.encode("utf-8"))
                    for k, v in response.headers.items()
                ]
            except Exception:
                self.raw_headers = []

        if redact:
            sanitized = sanitize_headers(response.headers, *redact)
            self.headers = sanitized

        if not hasattr(self, "history"):
            self.history = getattr(response, "history", [])

        if not hasattr(self, "original_url"):
            self.original_url = self.history[0].url if self.history else self.url

        if not hasattr(self, "final_url"):
            self.final_url = self.url

        if not hasattr(self, "host"):
            self.host = extract_host(self.original_url)

        if not hasattr(self, "elapsed"):
            self.elapsed = timedelta(0)

        if not hasattr(self, "links"):
            self.links = {}


class ClientProxy(wrapt.ObjectProxy):
    def __init__(
        self,
        wrapped: HTTPWrapClient,
        run_check: Callable[
            [httpmethod, Union[str, WrapURL], Sequence[Any], Mapping[str, Any]],
            Tuple[Sequence[Any], Mapping[str, Any]],
        ],
        response_proxy: Callable[[Any], WrapResponse],
    ) -> None:
        super().__init__(wrapped)
        self._run_check = run_check
        self._resp_proxy = response_proxy
        self._inject_methods()

    def request(
        self, method: httpmethod, url: Union[str, WrapURL], *args: Any, **kwargs: Any
    ) -> HTTPWrapResponse:
        nargs, nkwargs = self._run_check(method, url, args, kwargs)
        response = self.__wrapped__.request(method, url, *nargs, **nkwargs)
        return self._resp_proxy(response)

    def _inject_methods(self) -> None:
        for method in ALLOWED_METHODS:
            setattr(self, method, self._make_wrapped_method(method))

    def _make_wrapped_method(self, method_name: str):
        def wrapped_method(self, *args, **kwargs):
            url = args[0] if args else kwargs.get("url", "")
            nargs, nkwargs = self._run_check(method_name, url, args, kwargs)
            original = getattr(self.__wrapped__, method_name)
            response = original(*nargs, **nkwargs)
            return self._resp_proxy(response)

        return wrapped_method

    def __enter__(self) -> Any:
        if hasattr(self.__wrapped__, "__enter__"):
            return self.__wrapped__.__enter__()
        return self

    def __exit__(
        self,
        exc_type: Optional[Type[BaseException]],
        exc_value: Optional[BaseException],
        traceback: Optional[TracebackType],
    ) -> Optional[bool]:
        if hasattr(self.__wrapped__, "__exit__"):
            return self.__wrapped__.__exit__(exc_type, exc_value, traceback)
        return None

    async def __aenter__(self) -> Any:
        if hasattr(self.__wrapped__, "__aenter__"):
            return await self.__wrapped__.__aenter__()
        return self

    async def __aexit__(
        self,
        exc_type: Optional[Type[BaseException]],
        exc_value: Optional[BaseException],
        traceback: Optional[TracebackType],
    ) -> Optional[bool]:
        if hasattr(self.__wrapped__, "__aexit__"):
            return await self.__wrapped__.__aexit__(exc_type, exc_value, traceback)
        return None

    def __getattr__(self, name: str) -> Any:
        return getattr(self.__wrapped__, name)
