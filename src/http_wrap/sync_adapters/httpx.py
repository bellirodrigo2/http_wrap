from collections.abc import Callable
from contextlib import contextmanager
from dataclasses import dataclass
from typing import Any, ContextManager

import httpx

from http_wrap.request import HTTPRequestConfig
from http_wrap.response import ResponseInterface, ResponseProxy
from http_wrap.sync_adapters.basesync import SyncAdapter, SyncHttpSession


@contextmanager
def httpx_sync_session_factory(verify: bool):
    with httpx.Client(verify=verify) as session:
        yield session


@dataclass
class HttpxAdapter(SyncAdapter):
    make_session: Callable[..., ContextManager[SyncHttpSession]] = (
        httpx_sync_session_factory
    )

    def _make_args(self, config: HTTPRequestConfig) -> tuple[str, str, dict[str, Any]]:
        method, url, options = super()._make_args(config)
        options["follow_redirects"] = options.pop("allow_redirects", True)
        options.pop("verify", None)
        return method, url, options

    def request(self, config: HTTPRequestConfig) -> ResponseInterface:
        method, url, options = self._make_args(config)
        with self.make_session(verify=config.options.verify) as session:

            response = session.request(method=method, url=url, **options)
            return ResponseProxy(response)
