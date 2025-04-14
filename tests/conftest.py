import inspect
from typing import Any, Callable, Mapping, Optional, Tuple, Union

import httpx
import pytest
import requests
import responses
from pytest_httpx import HTTPXMock

from http_wrap.interfaces import WrapResponse


@pytest.fixture
def resquests_pack() -> Tuple[Callable[..., Any], Callable[..., Any]]:
    def make_response(
        method: str,
        url: str,
        headers: Mapping[str, Any],
        body: Union[str, bytes],
        status: int,
    ) -> responses.BaseResponse:

        return responses.add(
            method=method,
            url=url,
            body=body,
            status=status,
            headers=headers,
        )

    def http_request(
        method: str,
        url: str,
        headers: Mapping[str, Any],
        json: Optional[Mapping[str, str]] = None,
    ) -> requests.Response:
        with requests.Session() as session:
            resp = session.request(method, url, headers=headers, json=json)
            resp.raise_for_status()
            return resp

    return make_response, http_request


@pytest.fixture
def httpx_pack() -> Tuple[Callable[..., Any], Callable[..., Any]]:
    def make_response(
        httpx_mock: HTTPXMock,
        method: str,
        url: str,
        header: Mapping[str, Any],
        body: Union[str, bytes],
        status: int,
    ) -> HTTPXMock:
        httpx_mock.add_response(
            method=method,
            url=url,
            status_code=status,
            content=body,  # type: ignore
            headers=header,  # type: ignore
        )
        return httpx_mock

    def http_request(
        method: str,
        url: str,
        headers: Mapping[str, Any],
        json: Optional[Mapping[str, str]] = None,
    ) -> httpx.Response:

        with httpx.Client() as client:
            response = client.request(
                method=method, url=url, headers=headers, json=json
            )
            response.raise_for_status()
            return response

    return make_response, http_request


@pytest.fixture
def get_args_and_assert() -> Tuple[
    Mapping[str, Any],
    Mapping[str, Any],
    Callable[[WrapResponse], None],
]:

    host = "api.example.com"
    req: Mapping[str, Any] = {
        "method": "POST",
        "url": f"https://{host}/send",
        "headers": {"X-Test": "true"},
        "json": {"msg": "hello"},
    }
    resp: Mapping[str, Any] = {
        "body": '{"status": "ok", "echo": "hello"}',
        "status": 200,
        "content_type": "application/json",
        "extra_headers": {"X-Mock": "true"},
    }

    async def assert_response(response: WrapResponse) -> None:

        expected_raw_headers = [
            (b"content-type", b"application/json"),
            (b"x-mock", b"true"),
        ]

        assert response.status_code == resp["status"]
        assert response.reason == "OK"
        assert response.reason_phrase == "OK"
        assert response.ok is True
        assert response.is_success is True
        assert response.is_client_error is False
        assert response.is_error is False
        assert response.is_server_error is False
        assert response.is_redirect == False
        assert response.has_redirect_location is False
        assert response.is_informational is False
        assert response.url == req["url"]
        assert response.original_url == req["url"]
        assert response.final_url == req["url"]
        assert response.host == host
        assert response.encoding == "utf-8"
        assert response.headers["X-Mock"] == "true"
        # assert sorted(response.raw_headers) == sorted(expected_raw_headers)
        assert response.is_permanent_redirect == False  # NAO TEM NO HTTPX
        assert response.links == {}
        assert response.raise_for_status() is not None

        assert isinstance(response.history, list)
        assert response.elapsed.total_seconds() >= 0
        # assert hasattr(response.cookies, "get_dict") #NAO TEM EM HTTPX

        text = await response.text() if callable(response.text) else response.text
        assert text == resp["body"]

        content = (
            await response.content() if callable(response.content) else response.content
        )
        assert content == resp["body"].encode()

        json_data = (
            await response.json()
            if inspect.iscoroutinefunction(response.json)
            else response.json()
        )
        assert isinstance(json_data, dict)
        assert json_data["status"] == "ok"
        assert json_data["echo"] == "hello"

    return (req, resp, assert_response)
