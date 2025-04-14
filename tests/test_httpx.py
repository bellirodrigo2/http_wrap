import asyncio
from typing import Any, Callable, Mapping, Tuple

import httpx
import pytest
from pytest_httpx import HTTPXMock

from http_wrap.adapters.httpx_adapter import wrap_httpx_resp
from http_wrap.interfaces import WrapResponse


@pytest.mark.parametrize("is_async", [False, True])
def test_httpx_response_parametrized(
    is_async: bool,
    get_args_and_assert: Tuple[
        Mapping[str, Any],
        Mapping[str, Any],
        Callable[[WrapResponse], None],
    ],
    httpx_mock: HTTPXMock,
) -> None:
    reqmap, resp, assert_response = get_args_and_assert

    httpx_mock.add_response(
        method=reqmap["method"],
        url=reqmap["url"],
        status_code=resp["status"],
        content=resp["body"],
        headers=resp["extra_headers"],
    )

    def make_sync_request(req_map: Mapping[str, Any]) -> httpx.Response:
        with httpx.Client() as client:
            response = client.request(**req_map)
            response.raise_for_status()
            return response

    async def make_async_request_and_assert() -> None:
        async with httpx.AsyncClient() as client:
            response = await client.request(**reqmap)
            response.raise_for_status()

            proxy = wrap_httpx_resp(response)

            await assert_response(response)
            await assert_response(proxy)
            assert response.headers["content-length"] == "33"

    if is_async:
        asyncio.run(make_async_request_and_assert())
    else:
        response = make_sync_request(reqmap)
        proxy = wrap_httpx_resp(response)

        asyncio.run(assert_response(response))
        asyncio.run(assert_response(proxy))
