from collections.abc import Callable, Mapping
from contextlib import contextmanager
from dataclasses import dataclass
from typing import Any, ContextManager, Iterable, Protocol

from http_wrap.request import HTTPRequestConfig, HTTPRequestOptions, SyncHTTPRequest
from http_wrap.response import ResponseInterface, ResponseProxy


def sublist(lista: list[Any], n: int) -> list[list[Any]]:
    return [lista[i : i + n] for i in range(0, len(lista), n)]


class SyncHttpSession(Protocol):
    def request(self, method: str, url: str, **kwargs: Any) -> Any: ...


def std_make_args(config: HTTPRequestConfig) -> tuple[str, str, dict[str, Any]]:
    config.validate()
    request_kwargs = config.options.dump(
        exclude_none=True, convert_cookies_to_dict=True
    )
    return config.method, config.url, request_kwargs


@dataclass
class SyncAdapter(SyncHTTPRequest):
    make_session: Callable[[HTTPRequestOptions], ContextManager[SyncHttpSession]]
    make_args: Callable[[HTTPRequestConfig], tuple[str, str, dict[str, Any]]] = (
        std_make_args
    )

    def request(self, config: HTTPRequestConfig) -> ResponseInterface:

        with self.make_session(config.options) as session:
            method, url, options = self.make_args(config)
            response = session.request(method=method, url=url, **options)
            return ResponseProxy(response)

    def requests(
        self, configs: list[HTTPRequestConfig], max: int = 1
    ) -> Iterable[ResponseInterface]:

        with self.make_session() as session:

            for batch_configs in sublist(configs, max):
                responses: list[ResponseInterface] = []
                for config in batch_configs:
                    method, url, options = self.make_args(config)
                    response = session.request(method=method, url=url, **options)
                    responses.append(ResponseProxy(response))
                yield responses
