import re
from collections.abc import Callable
from contextlib import contextmanager
from dataclasses import dataclass
from http import HTTPStatus
from inspect import stack
from types import MethodType
from typing import ContextManager
from urllib.parse import urlparse

import requests
import wrapt

from http_wrap.adapters.utils import (
    extract_host,
    in_between,
    normalize_response_headers,
)

# from http_wrap.request import HTTPRequestOptions
# from http_wrap.sync_adapters.basesync import SyncAdapter, SyncHttpSession


# @contextmanager
# def requests_session_factory(_: HTTPRequestOptions):
#     with requests.Session() as session:
#         yield session


def wrap_requests_resp(response: requests.Response):

    proxy = wrapt.ObjectProxy(response)

    status = HTTPStatus(response.status_code)

    proxy.reason_phrase = status.phrase

    proxy.is_informational = status.is_informational

    proxy.is_success = status.is_success

    proxy.is_client_error = status.is_client_error

    proxy.is_server_error = status.is_server_error

    proxy.is_error = status.is_client_error or status.is_server_error

    proxy.has_redirect_location = (
        "Location" in response.headers
        and response.status_code
        in (
            HTTPStatus.MOVED_PERMANENTLY,
            HTTPStatus.FOUND,
            HTTPStatus.SEE_OTHER,
            HTTPStatus.TEMPORARY_REDIRECT,
            HTTPStatus.PERMANENT_REDIRECT,
        )
    )

    original_raise = response.raise_for_status

    def raise_for_status_print(resp) -> str:
        original_raise()
        return resp

    proxy.raise_for_status = MethodType(raise_for_status_print, proxy)

    proxy.original_url = response.history[0].url if response.history else response.url
    proxy.final_url = response.url

    proxy.host = extract_host(proxy.original_url)

    normalize_response_headers(proxy.headers, response.content)

    proxy.raw_headers = [
        (k.lower().encode("utf-8"), v.encode("utf-8"))
        for k, v in response.headers.items()
    ]
    return proxy


# @dataclass
# class RequestsAdapter(SyncAdapter):
#     make_session: Callable[[HTTPRequestOptions], ContextManager[SyncHttpSession]] = (
#         requests_session_factory
#     )
