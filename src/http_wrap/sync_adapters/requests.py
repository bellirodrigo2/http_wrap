from collections.abc import Callable
from contextlib import contextmanager
from dataclasses import dataclass
from typing import ContextManager

import requests

from http_wrap.request import HTTPRequestOptions
from http_wrap.sync_adapters.basesync import SyncAdapter, SyncHttpSession


@contextmanager
def requests_session_factory(_: HTTPRequestOptions):
    with requests.Session() as session:
        yield session


@dataclass
class RequestsAdapter(SyncAdapter):
    make_session: Callable[[HTTPRequestOptions], ContextManager[SyncHttpSession]] = (
        requests_session_factory
    )
