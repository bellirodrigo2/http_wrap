from collections.abc import Callable, Mapping
from contextlib import contextmanager
from dataclasses import dataclass
from typing import Any, ContextManager

import httpx

from http_wrap.request import HTTPRequestConfig, HTTPRequestOptions
from http_wrap.sync_adapters.basesync import SyncAdapter, SyncHttpSession, std_make_args


@contextmanager
def httpx_sync_session_factory(option: HTTPRequestOptions):
    verify = option.verify
    with httpx.Client(verify=verify) as session:
        yield session


def httpx_make_args(config: HTTPRequestConfig):
    method, url, options = std_make_args(config)
    options["follow_redirects"] = options.pop("allow_redirects", True)
    options.pop("verify", True)
    return method, url, options


@dataclass
class HttpxAdapter(SyncAdapter):
    make_session: Callable[..., ContextManager[SyncHttpSession]] = (
        httpx_sync_session_factory
    )
    make_args: Callable[[HTTPRequestConfig], tuple[str, str, dict[str, Any]]] = (
        httpx_make_args
    )
