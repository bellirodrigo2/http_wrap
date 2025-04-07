import pytest
import httpx
from urllib.parse import urlencode
from http_wrap.sync_adapters import HttpxAdapter
from src.http_wrap import HTTPRequestConfig, HTTPRequestOptions

# Fixture para o client
@pytest.fixture
def client():
    return HttpxAdapter()


@pytest.mark.parametrize(
    "method, url, options, expected_status, expected_response_text",
    [
        ("GET", "https://example.com/api", HTTPRequestOptions(params={"q": "test"}), 200, "ok"),
        ("POST", "https://example.com/api", HTTPRequestOptions(body={"key": "val"}), 200, "ok"),
        ("PUT", "https://example.com/api", HTTPRequestOptions(body={"update": True}), 200, "ok"),
        ("PATCH", "https://example.com/api", HTTPRequestOptions(body={"patch": "val"}), 200, "ok"),
        ("DELETE", "https://example.com/api", HTTPRequestOptions(), 200, "ok"),
        ("HEAD", "https://example.com/api", HTTPRequestOptions(), 200, ""),
        ("POST", "https://example.com/api", HTTPRequestOptions(body={"invalid": True}), 400, "bad request"),
    ],
)
def test_sync_httpx_methods(client, method, url, options, expected_status, expected_response_text, httpx_mock):
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
            headers={"Content-Type": "application/json"}
        )
    else:
        httpx_mock.add_response(
            method=method,
            url=full_url,
            status_code=expected_status,
            content=expected_response_text.encode('utf-8'),
            headers={"Content-Type": "application/json"}
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
