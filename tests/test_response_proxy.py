from datetime import timedelta

import httpx
import pytest
import responses
from aiohttp import ClientSession
from aioresponses import aioresponses

from http_wrap.async_adapters.aiohttp import make_response
from http_wrap.response import ResponseInterface, ResponseProxy
from http_wrap.security import Headers
from http_wrap.settings import configure


@responses.activate
def test_response_proxy_with_requests():
    responses.add(
        responses.GET,
        "https://example.com",
        json={"message": "ok"},
        headers={"Authorization": "secret", "X-Test": "value"},
        status=200,
    )

    import requests

    resp = requests.get("https://example.com")
    proxy = ResponseProxy(resp)

    assert isinstance(proxy, ResponseInterface)
    assert proxy.status_code == 200
    assert proxy.text
    assert proxy.content
    assert proxy.url.rstrip("/") == "https://example.com"
    assert isinstance(proxy.headers, Headers)
    assert "x-test" in proxy.headers
    assert proxy.headers["x-test"] == "value"
    assert "Authorization" not in str(proxy.headers)
    assert "<redacted>" in str(proxy.headers)
    assert proxy.headers.raw()["authorization"] == "secret"
    assert isinstance(proxy.cookies, dict)
    assert isinstance(proxy.json(), dict)
    assert isinstance(proxy.encoding, str)
    assert isinstance(proxy.elapsed, timedelta)
    assert isinstance(proxy.history, list)


@pytest.mark.asyncio
async def test_response_proxy_with_aiohttp():
    with aioresponses() as mocked:
        mocked.get(
            "https://example.com",
            status=200,
            payload={"message": "ok"},
            headers={"Authorization": "top-secret", "X-Test": "abc"},
        )

        async with ClientSession() as session:
            async with session.get("https://example.com") as resp:
                wrapped = await make_response(resp)
                proxy = ResponseProxy(wrapped)

                assert isinstance(proxy, ResponseInterface)
                assert proxy.status_code == 200
                assert proxy.text
                assert proxy.content
                assert proxy.url.rstrip("/") == "https://example.com"
                assert isinstance(proxy.headers, Headers)
                assert "x-test" in proxy.headers
                assert proxy.headers["x-test"] == "abc"
                assert "Authorization" not in str(proxy.headers)
                assert "<redacted>" in str(proxy.headers)
                assert proxy.headers.raw()["authorization"] == "top-secret"
                assert isinstance(proxy.cookies, dict)
                assert isinstance(proxy.json(), dict)
                assert isinstance(proxy.encoding, str)
                assert isinstance(proxy.elapsed, timedelta)
                assert isinstance(proxy.history, list)


def test_response_proxy_with_httpx(httpx_mock):
    httpx_mock.add_response(
        method="GET",
        url="https://example.com",
        json={"message": "ok"},
        headers={"Authorization": "hidden-token", "X-Test": "123"},
    )

    resp = httpx.get("https://example.com")
    proxy = ResponseProxy(resp)

    assert isinstance(proxy, ResponseInterface)
    assert proxy.status_code == 200
    assert proxy.text
    assert proxy.content
    assert proxy.url.rstrip("/") == "https://example.com"
    assert isinstance(proxy.headers, Headers)
    assert "x-test" in proxy.headers
    assert proxy.headers["x-test"] == "123"
    assert "Authorization" not in str(proxy.headers)
    assert "<redacted>" in str(proxy.headers)
    assert proxy.headers.raw()["authorization"] == "hidden-token"
    assert isinstance(proxy.cookies, dict)
    assert isinstance(proxy.json(), dict)
    assert isinstance(proxy.encoding, str)
    assert isinstance(proxy.elapsed, timedelta)
    assert isinstance(proxy.history, list)


def test_custom_redact_headers(httpx_mock):
    # Configure custom headers for redaction
    configure(redact_headers=["X-Custom-Header"])

    httpx_mock.add_response(
        method="GET",
        url="https://example.com",
        json={"message": "ok"},
        headers={
            "X-Custom-Header": "sensitive-value",
            "Authorization": "should-not-be-redacted",
        },
    )

    resp = httpx.get("https://example.com")
    proxy = ResponseProxy(resp)

    # X-Custom-Header should be redacted, while Authorization remains intact if not configured to redact
    assert "<redacted>" in str(proxy.headers.get("x-custom-header"))
    assert proxy.headers.get("authorization") == "should-not-be-redacted"
