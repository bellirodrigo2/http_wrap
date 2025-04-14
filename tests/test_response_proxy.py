from http.client import responses
from typing import Any, Callable, Tuple

import pytest
import responses
from pytest_httpx import HTTPXMock

from http_wrap.proxies import ResponseProxy
from tests.conftest import ReqPack

host = "localhost"
url = f"http://{host}/send"
reqh = {"X-Test": "true"}
json = {"msg": "hello"}
body = '{"status": "ok", "echo": "hello"}'
resph = {"X-Mock": "true"}


def make_pack(method: str, status: int) -> ReqPack:
    return ReqPack(
        method=method,
        url=url,
        req_headers=reqh,
        json=json,
        resp_headers=resph,
        body=body,
        status=status,
    )


oks = [
    make_pack("GET", 200),
    make_pack("POST", 201),
    make_pack("PATCH", 202),
    make_pack("PUT", 203),
]


def base_asserts(resp: Any, proxy: ResponseProxy, pack: ReqPack) -> None:

    assert resp == proxy.raise_for_status()

    assert resp.status_code == pack.status
    assert resp.status == pack.status

    assert proxy.status_code == pack.status
    assert proxy.status == pack.status

    assert proxy.reason.upper() == proxy.reason_phrase


@pytest.mark.parametrize(
    "pack",
    oks,
)
@responses.activate
def test_ok_requests(
    pack: ReqPack,
    requests_pack: Tuple[Callable[..., Any], Callable[..., Any]],
) -> None:

    make_response_requests, http_request_requests = requests_pack
    make_response_requests(
        pack.method, pack.url, pack.resp_headers, pack.body, pack.status
    )
    resp = http_request_requests(pack.method, pack.url, pack.req_headers, pack.json)
    proxy = ResponseProxy(resp)

    base_asserts(resp, proxy, pack)
    assert resp.ok == True
    assert proxy.ok == True

    assert resp.is_success == True
    assert proxy.is_success == True


@pytest.mark.parametrize(
    "pack",
    oks,
)
def test_ok_httpx_sync(
    pack: ReqPack,
    httpx_pack: Tuple[Callable[..., Any], Callable[..., Any]],
    httpx_mock: HTTPXMock,
) -> None: ...
