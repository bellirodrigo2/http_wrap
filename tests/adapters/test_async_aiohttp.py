from datetime import timedelta

import aiohttp
import pytest
from aioresponses import aioresponses

from http_wrap.async_adapters import AioHttpAdapter
from http_wrap.async_adapters.aiohttp import make_response
from http_wrap.request import HTTPRequestConfig, HTTPRequestOptions, ResponseInterface
from http_wrap.response import ResponseProxy


@pytest.fixture
async def adapter():
    adapter = AioHttpAdapter(verify_ssl=False)
    await adapter.init_session()
    yield adapter
    await adapter.close_session()


BASE_URL = "https://test.com/resource"


def make_config(
    method: str, url: str, payload=None, params=None, headers=None
) -> HTTPRequestConfig:
    options = HTTPRequestOptions(
        json=payload, params=params or {}, headers=headers or {}
    )
    return HTTPRequestConfig(method=method, url=url, options=options)


# --- TESTES request() unitário ---


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "method, expected_status, payload",
    [
        ("GET", 200, None),
        ("POST", 201, {"name": "test"}),
        ("PUT", 200, {"name": "updated"}),
        ("PATCH", 200, {"patch": True}),
        ("DELETE", 204, None),
        ("HEAD", 200, None),
    ],
)
async def test_http_methods_success(adapter, method, expected_status, payload):
    config = make_config(method, BASE_URL, payload)

    with aioresponses() as mock:
        mock_method = getattr(mock, method.lower())
        mock_method(BASE_URL, status=expected_status)

        response: ResponseInterface = await adapter.request(config)

        assert response.status_code == expected_status
        assert isinstance(response.text, str)
        assert isinstance(response.content, bytes)

    await adapter.close_session()


@pytest.mark.asyncio
async def test_request_with_params_and_headers(adapter):
    config = make_config(
        "GET",
        f"{BASE_URL}/withparams",
        params={"q": "query"},
        headers={"X-Test": "yes"},
    )

    with aioresponses() as mock:
        mock.get(f"{BASE_URL}/withparams?q=query", status=200)

        response = await adapter.request(config)
        assert response.status_code == 200

    await adapter.close_session()


@pytest.mark.asyncio
async def test_request_raises_client_error(adapter):
    config = make_config("GET", BASE_URL)

    with aioresponses() as mock:
        mock.get(BASE_URL, exception=aiohttp.ClientError("Boom"))

        with pytest.raises(aiohttp.ClientError, match="Boom"):
            await adapter.request(config)

    await adapter.close_session()


@pytest.mark.asyncio
async def test_response_proxy_with_aiohttp():
    with aioresponses() as mocked:
        mocked.get(
            "https://example.com",
            status=200,
            payload={"message": "ok"},
            headers={"Authorization": "top-secret", "X-Test": "abc"},
        )

        async with aiohttp.ClientSession() as session:
            async with session.get("https://example.com") as resp:
                wrapped = await make_response(resp)
                proxy = ResponseProxy(wrapped)

                assert isinstance(proxy, ResponseInterface)
                assert proxy.status_code == 200
                assert proxy.text
                assert proxy.content
                assert proxy.url.rstrip("/") == "https://example.com"
                # assert isinstance(proxy.headers, Headers)
                assert "x-test" in proxy.headers
                assert proxy.headers["x-test"] == "abc"
                assert "Authorization" not in str(proxy.headers)
                assert "<redacted>" in str(proxy.headers)
                assert proxy.headers.raw["authorization"] == "top-secret"
                assert isinstance(proxy.cookies, dict)
                assert isinstance(proxy.json(), dict)
                assert isinstance(proxy.encoding, str)
                assert isinstance(proxy.elapsed, timedelta)
                assert isinstance(proxy.history, list)
