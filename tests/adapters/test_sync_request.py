from urllib.parse import urlencode

import pytest
import responses

from http_wrap.sync_adapters import RequestsAdapter
from src.http_wrap import HTTPRequestConfig, HTTPRequestOptions


# Fixture para o client
@pytest.fixture
def client():
    return RequestsAdapter()


@pytest.mark.parametrize(
    "method, url, options, expected_status, expected_response_text",
    [
        # GET com params: a URL final incluirá a query string.
        (
            "get",
            "https://example.com/api",
            HTTPRequestOptions(params={"q": "test"}),
            200,
            "ok",
        ),
        # POST com body
        (
            "post",
            "https://example.com/api",
            HTTPRequestOptions(json={"key": "val"}),
            200,
            "ok",
        ),
        # PUT com body
        (
            "put",
            "https://example.com/api",
            HTTPRequestOptions(json={"update": True}),
            200,
            "ok",
        ),
        # PATCH com body
        (
            "patch",
            "https://example.com/api",
            HTTPRequestOptions(json={"patch": "val"}),
            200,
            "ok",
        ),
        # DELETE sem body
        ("delete", "https://example.com/api", HTTPRequestOptions(), 200, "ok"),
        # HEAD sem corpo: espera retorno vazio
        ("head", "https://example.com/api", HTTPRequestOptions(), 200, ""),
        # POST com body, mas simulando erro (400)
        (
            "post",
            "https://example.com/api",
            HTTPRequestOptions(json={"invalid": True}),
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
    if method == "head":
        responses.add(
            method=method.upper(),
            url=full_url,
            status=expected_status,
            content_type="application/json",
        )
    else:
        responses.add(
            method=method.upper(),
            url=full_url,
            json=expected_response_text,
            status=expected_status,
            content_type="application/json",
        )

    # Cria o config e chama o método request do adaptador.
    config = HTTPRequestConfig(method=method, url=url, options=options)
    response = client.request(config)

    # Verifica o status code
    assert response.status_code == expected_status

    # Se não for HEAD, verifica o conteúdo (text)
    if method != "head":
        assert response.json() == expected_response_text

    # Verifica que a URL retornada inclui a query string se houver params.
    assert response.url == full_url
