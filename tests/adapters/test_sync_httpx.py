from datetime import timedelta
from urllib.parse import urlencode

import httpx
import pytest

from http_wrap import HTTPRequestConfig, HTTPRequestOptions
from http_wrap.response import ResponseInterface, ResponseProxy
from http_wrap.sync_adapters import HttpxAdapter


# Fixture para o client
@pytest.fixture
def client():
    return HttpxAdapter()


@pytest.mark.parametrize(
    "method, url, options, expected_status, expected_response_text",
    [
        (
            "GET",
            "https://example.com/api",
            HTTPRequestOptions(params={"q": "test"}),
            200,
            "ok",
        ),
        (
            "POST",
            "https://example.com/api",
            HTTPRequestOptions(json={"key": "val"}),
            200,
            "ok",
        ),
        (
            "PUT",
            "https://example.com/api",
            HTTPRequestOptions(json={"update": True}),
            200,
            "ok",
        ),
        (
            "PATCH",
            "https://example.com/api",
            HTTPRequestOptions(json={"patch": "val"}),
            200,
            "ok",
        ),
        ("DELETE", "https://example.com/api", HTTPRequestOptions(), 200, "ok"),
        ("HEAD", "https://example.com/api", HTTPRequestOptions(), 200, ""),
        (
            "POST",
            "https://example.com/api",
            HTTPRequestOptions(json={"invalid": True}),
            400,
            "bad request",
        ),
    ],
)
def test_sync_httpx_methods(
    client, method, url, options, expected_status, expected_response_text, httpx_mock
):
    # Monte a URL completa considerando que, se houver params, o httpx monta a query string
    full_url = url
    if options.params:
        full_url = f"{url}?{urlencode(options.params)}"

    # Use httpx_mock para simular respostas
    if method.upper() == "HEAD":
        httpx_mock.add_response(
            method=method,
            url=full_url,
            status_code=expected_status,
            content=b"",
            headers={"Content-Type": "application/json"},
        )
    else:
        httpx_mock.add_response(
            method=method,
            url=full_url,
            status_code=expected_status,
            content=expected_response_text.encode("utf-8"),
            headers={"Content-Type": "application/json"},
        )

    # Cria o config e chama o método request do adaptador.
    config = HTTPRequestConfig(method=method, url=url, options=options)

    # Aqui estamos modificando a chamada para se adequar ao httpx
    response = client.request(config)

    # Verifica o status code
    assert response.status_code == expected_status

    # Se não for HEAD, verifica o conteúdo (texto)
    if method.upper() != "HEAD":
        assert response.text == expected_response_text
    else:
        assert response.text == ""

    # Verifica que a URL retornada inclui a query string se houver params
    assert response.url == full_url


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
    # assert isinstance(proxy.headers, Headers)
    assert "x-test" in proxy.headers
    assert proxy.headers["x-test"] == "123"
    assert "Authorization" not in str(proxy.headers)
    assert "<redacted>" in str(proxy.headers)
    # assert proxy.headers.raw["authorization"] == "hidden-token"
    assert isinstance(proxy.cookies, dict)
    assert isinstance(proxy.json(), dict)
    assert isinstance(proxy.encoding, str)
    assert isinstance(proxy.elapsed, timedelta)
    assert isinstance(proxy.history, list)
