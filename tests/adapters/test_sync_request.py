from urllib.parse import urlencode

import pytest
import responses

from http_wrap.sync_adapters import RequestsAdapter
from src.http_wrap import HTTPRequestConfig, HTTPRequestOptions


# Fixture para o client
@pytest.fixture
def client():
    return RequestsAdapter()


# Parametrização para vários métodos e cenários:
@pytest.mark.parametrize(
    "method, url, options, expected_status, expected_response_text",
    [
        # GET com params: a URL final incluirá a query string.
        (
            "GET",
            "https://example.com/api",
            HTTPRequestOptions(params={"q": "test"}),
            200,
            "ok",
        ),
        # POST com body
        (
            "POST",
            "https://example.com/api",
            HTTPRequestOptions(body={"key": "val"}),
            200,
            "ok",
        ),
        # PUT com body
        (
            "PUT",
            "https://example.com/api",
            HTTPRequestOptions(body={"update": True}),
            200,
            "ok",
        ),
        # PATCH com body
        (
            "PATCH",
            "https://example.com/api",
            HTTPRequestOptions(body={"patch": "val"}),
            200,
            "ok",
        ),
        # DELETE sem body
        ("DELETE", "https://example.com/api", HTTPRequestOptions(), 200, "ok"),
        # HEAD sem corpo: espera retorno vazio
        ("HEAD", "https://example.com/api", HTTPRequestOptions(), 200, ""),
        # POST com body, mas simulando erro (400)
        (
            "POST",
            "https://example.com/api",
            HTTPRequestOptions(body={"invalid": True}),
            400,
            "bad request",
        ),
    ],
)
@responses.activate
def test_sync_http_methods(
    client, method, url, options, expected_status, expected_response_text
):
    # Monte a URL completa considerando que, se houver params, o requests monta a query string
    full_url = url
    if options.params:
        full_url = f"{url}?{urlencode(options.params)}"

    # Para HEAD, não se define body, pois não deve haver conteúdo.
    if method.upper() == "HEAD":
        responses.add(
            method=method,
            url=full_url,
            status=expected_status,
            content_type="application/json",
        )
    else:
        responses.add(
            method=method,
            url=full_url,
            body=expected_response_text,
            status=expected_status,
            content_type="application/json",
        )

    # Cria o config e chama o método request do adaptador.
    config = HTTPRequestConfig(method=method, url=url, options=options)
    response = client.request(config)

    # Verifica o status code
    assert response.status_code == expected_status

    # Se não for HEAD, verifica o conteúdo (text)
    if method.upper() != "HEAD":
        assert response.text == expected_response_text
    else:
        assert response.text == ""

    # Verifica que a URL retornada inclui a query string se houver params.
    assert response.url == full_url
