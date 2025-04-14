from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any, Callable, Optional, Tuple, Union

import pytest
from pytest_httpx import HTTPXMock


@dataclass
class ReqPack:
    method: str
    url: str

    req_headers: Mapping[str, Any]
    json: Optional[Mapping[str, str]]
    data: Optional[Mapping[str, str]]
    params: Optional[Mapping[str, str]]

    resp_headers: Mapping[str, Any]
    body: Union[str, bytes]
    status: int


@pytest.mark.parametrize(
    ["pack"],
    [None, None],
)
def test_ok_response(
    pack: ReqPack,
    requests_pack: Tuple[Callable[..., Any], Callable[..., Any]],
    httpx_mock: HTTPXMock,
) -> None:

    response_requests, request_requests = requests_pack

    response_requests(method, url)
