import aiohttp
import httpx
import pytest
import requests
from aioresponses import aioresponses

from http_wrap.async_adapters.aiohttp import make_response
from http_wrap.response import ResponseInterface, ResponseProxy
from http_wrap.security import Headers


@pytest.fixture
def responses_fixture():
    import responses

    with responses.RequestsMock() as rsps:
        yield rsps


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "client_lib, mock_lib",
    [
        ("requests", "responses_fixture"),
        ("httpx", "httpx_mock"),
        ("aiohttp", "aioresponses"),
    ],
)
async def test_response_proxy_generic(client_lib, mock_lib, request):
    if client_lib == "requests":
        responses = request.getfixturevalue("responses_fixture")
        responses.add(
            responses.GET,
            "https://test.local",
            headers={"Location": "https://test.local/final"},
            status=302,
        )
        responses.add(
            responses.GET,
            "https://test.local/final",
            headers={
                "Authorization": "secret",
                "X-Test": "ok",
                "Set-Cookie": "sessionid=abc123; Path=/; HttpOnly",
            },
            body='{"message": "hello"}',
            status=200,
            content_type="application/json",
        )
        resp = requests.get("https://test.local", allow_redirects=True)
        proxy = ResponseProxy(resp)

    elif client_lib == "httpx":
        httpx_mock = request.getfixturevalue("httpx_mock")
        httpx_mock.add_response(
            method="GET",
            url="https://test.local",
            status_code=302,
            headers={"Location": "https://test.local/final"},
        )
        httpx_mock.add_response(
            method="GET",
            url="https://test.local/final",
            status_code=200,
            headers={
                "Authorization": "secret",
                "X-Test": "ok",
                "Set-Cookie": "sessionid=abc123; Path=/; HttpOnly",
            },
            json={"message": "hello"},
        )
        resp = httpx.get("https://test.local", follow_redirects=True)
        proxy = ResponseProxy(resp)

    elif client_lib == "aiohttp":
        with aioresponses() as m:
            m.get(
                "https://test.local",
                status=302,
                headers={"Location": "https://test.local/final"},
            )
            m.get(
                "https://test.local/final",
                status=200,
                headers={
                    "Authorization": "secret",
                    "X-Test": "ok",
                    "Set-Cookie": "sessionid=abc123; Path=/; HttpOnly",
                    "Content-Type": "application/json",
                },
                body='{"message": "hello"}',
            )

            async with aiohttp.ClientSession() as session:
                async with session.get(
                    "https://test.local", allow_redirects=True
                ) as resp:
                    proxy = await make_response(resp)

    # Interface compliance
    assert isinstance(proxy, ResponseInterface)
    assert isinstance(proxy.headers, Headers)
    assert proxy.headers["X-Test"] == "ok"
    assert "authorization" in proxy.headers  # normalizado para lowercase
    assert "<redacted>" in str(proxy.headers)

    assert proxy.status_code == 200
    assert proxy.json()["message"] == "hello"
    assert proxy.url.endswith("/final")
    assert isinstance(proxy.cookies, dict)
    assert isinstance(proxy.elapsed, (int, float, type(proxy.elapsed)))
    assert isinstance(proxy.history, list)
    # assert isinstance(proxy.reason, str)
