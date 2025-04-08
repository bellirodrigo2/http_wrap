from collections.abc import Callable
from contextlib import contextmanager
from dataclasses import dataclass, field
from typing import ContextManager

import requests

from http_wrap.sync_adapters.basesync import SyncAdapter, SyncHttpSession


@contextmanager
def requests_session_factory():
    with requests.Session() as session:
        yield session


@dataclass
class RequestsAdapter(SyncAdapter):
    make_session: Callable[[], ContextManager[SyncHttpSession]] = (
        requests_session_factory
    )
