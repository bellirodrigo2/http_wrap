import asyncio
import inspect
from typing import Any, Type, Union
from urllib.parse import urlparse

import aiohappyeyeballs
import aiohttp
import httpx
import requests


def in_between(code: int, start: int, end: int) -> bool:
    return start <= code <= end


def get_constructor_args(cls: Type[Any]) -> list[str]:
    sig = inspect.signature(cls.__init__)
    args = [name for name in sig.parameters.keys() if name != "self"]
    return args or cls.__attrs__


def extract_host(url: str) -> str:

    parsed_url = urlparse(str(url))
    host = parsed_url.hostname

    if host is None:
        raise ValueError(f"Invalid original_url, no host found: {url}")

    return host


def normalize_response_headers(
    headers: dict, body: Union[str, bytes, dict, list, None]
) -> None:
    def has_header(name: str) -> bool:
        return any(k.lower() == name.lower() for k in headers)

    # Normalize Content-Type
    if not has_header("Content-Type"):
        if isinstance(body, (dict, list)):
            headers["Content-Type"] = "application/json"
        elif isinstance(body, str):
            headers["Content-Type"] = "text/plain; charset=utf-8"
        elif isinstance(body, bytes):
            headers["Content-Type"] = "application/octet-stream"

    # Normalize Content-Length
    if not has_header("Content-Length"):
        if isinstance(body, str):
            headers["Content-Length"] = str(len(body.encode("utf-8")))
        elif isinstance(body, bytes):
            headers["Content-Length"] = str(len(body))


if __name__ == "__main__":

    httpx_args = get_constructor_args(httpx.Client)
    with httpx.Client() as client:
        print(type(client))
    print(httpx_args)

    req_args = get_constructor_args(requests.Session)
    with requests.Session() as session:
        print(type(session))
    print(req_args)

    aiohttp_args = get_constructor_args(aiohttp.ClientSession)

    async def run():
        async with aiohttp.ClientSession() as session:
            print(type(session))

    asyncio.run(run())
    print(aiohttp_args)

    print(inspect(httpx.Client))
