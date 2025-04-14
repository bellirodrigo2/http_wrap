from typing import Any, Callable, Mapping, Tuple

import pytest
import requests
import responses

from http_wrap.adapters.requests_adapter import wrap_requests_resp
from http_wrap.interfaces import WrapResponse


@responses.activate
async def test_requests_response(
    get_args_and_assert: Tuple[
        Mapping[str, Any],
        Mapping[str, Any],
        Callable[[WrapResponse], None],
    ],
) -> None:

    reqmap, resp, assert_response = get_args_and_assert

    responses.add(
        method=reqmap["method"],
        url=reqmap["url"],
        body=resp["body"],
        status=resp["status"],
        content_type=resp["content_type"],
        headers=resp["extra_headers"],
    )

    def make_request(req_map: Mapping[str, Any]) -> requests.Response:
        req = requests.Request(**req_map)
        prepared = req.prepare()
        session = requests.Session()
        resp = session.send(prepared)
        resp.raise_for_status()
        return resp

    response = make_request(reqmap)

    proxy = wrap_requests_resp(response)
    await assert_response(response)
    await assert_response(proxy)
    #     assert len(responses.calls) == 1
    # sent = responses.calls[0].request
    # assert sent.method == "POST"
    # assert sent.url == "https://api.example.com/send"
    # assert sent.headers["X-Test"] == "true"
    # assert sent.body == b'{"msg": "hello"}'

    # assert isinstance(response.request, requests.PreparedRequest)
