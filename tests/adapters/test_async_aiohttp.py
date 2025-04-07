import aiohttp
import pytest
from aioresponses import aioresponses

from http_wrap.async_adapters import AioHttpAdapter
from http_wrap.request import HTTPRequestConfig, HTTPRequestOptions, ResponseInterface


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
