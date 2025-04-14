import asyncio
from contextlib import AbstractAsyncContextManager, AbstractContextManager
from typing import Any
from unittest.mock import AsyncMock, Mock

import pytest

from http_wrap.configs import HTTPWrapConfig
from http_wrap.httpwrap import make_client_session
from http_wrap.interfaces import HTTPWrapClient


def test_make_client_session_sync() -> None:
    mock_sessionmaker = Mock()
    mock_session = Mock(spec=HTTPWrapClient)
    mock_sessionmaker.return_value = mock_session

    config = HTTPWrapConfig()

    session_ctx = make_client_session(mock_sessionmaker, config)

    assert isinstance(session_ctx, AbstractContextManager)


@pytest.mark.asyncio
async def test_make_client_session_async() -> None:
    mock_async_session = AsyncMock(spec=HTTPWrapClient)

    async def async_sessionmaker(**kwargs: Any) -> AsyncMock:
        return mock_async_session

    config = HTTPWrapConfig()

    session_ctx = make_client_session(async_sessionmaker, config)

    assert isinstance(session_ctx, AbstractAsyncContextManager)

    async with session_ctx as client:
        from http_wrap.proxies import ClientProxy

        assert isinstance(client, ClientProxy)
        assert client.__wrapped__ is mock_async_session
