from datetime import timedelta
from http import HTTPStatus
from types import MethodType
from typing import Mapping

import wrapt
from aiohttp import ClientResponse

from http_wrap.adapters.utils import normalize_response_headers

#  o aiohttp não permite usar data e json juntos em uma mesma chamada.
# Ele é mais rígido: ou você manda
# data (como application/x-www-form-urlencoded) ou json (como application/json)
# nunca ambos.


def wrap_aiohttp_response(response: ClientResponse):
    proxy = wrapt.ObjectProxy(response)

    def in_between(start: int, end: int) -> bool:
        return start <= response.status < end

    proxy.reason_phrase = HTTPStatus(response.status).phrase

    # Status helpers
    proxy.ok = in_between(200, 400)
    proxy.is_informational = in_between(100, 200)
    proxy.is_success = in_between(200, 300)
    proxy.is_redirect = in_between(300, 400)
    proxy.is_error = in_between(400, 600)
    proxy.is_client_error = in_between(400, 500)
    proxy.is_server_error = in_between(500, 600)

    proxy.is_permanent_redirect = (
        "location" in response.headers
        and response.status
        in (HTTPStatus.MOVED_PERMANENTLY, HTTPStatus.PERMANENT_REDIRECT)
    )

    proxy.has_redirect_location = (
        "location" in response.headers
        and response.status
        in {
            HTTPStatus.MOVED_PERMANENTLY,
            HTTPStatus.FOUND,
            HTTPStatus.SEE_OTHER,
            HTTPStatus.TEMPORARY_REDIRECT,
            HTTPStatus.PERMANENT_REDIRECT,
        }
    )
    proxy.status_code = response.status
    proxy.elapsed = timedelta(0)  # Aiohttp não fornece nativamente
    proxy.links = {}  # Pode ser extraído do header Link se quiser
    proxy.history = []  # Não há redirect history automático

    async def raise_for_status_print(resp):
        resp.raise_for_status()
        return resp

    proxy.raise_for_status = MethodType(raise_for_status_print, proxy)

    proxy.original_url = response.url
    proxy.final_url = response.real_url

    normalize_response_headers(proxy.headers, response.content)

    return proxy
