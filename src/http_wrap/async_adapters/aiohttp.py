import asyncio
from collections.abc import AsyncGenerator
from dataclasses import dataclass, field
from datetime import timedelta
from typing import Any, Optional

import aiohttp

from http_wrap.request import AsyncHTTPRequest, HTTPRequestConfig
from http_wrap.response import ResponseInterface, ResponseProxy


@dataclass(frozen=True)
class AiohttpResponse:
    status_code: int
    text: str
    content: bytes
    url: str
    headers: dict[str, str] = field(default_factory=dict)
    cookies: dict[str, str] = field(default_factory=dict)
    encoding: str = "utf-8"
    elapsed: timedelta = field(default_factory=timedelta)
    history: list["ResponseInterface"] = field(default_factory=list)
    reason: str = ""

    def json(self) -> dict[str, Any]:
        import json

        try:
            return json.loads(self.text)
        except json.JSONDecodeError:
            return {}


async def make_response(resp: aiohttp.ClientResponse) -> ResponseInterface:
    text = await resp.text()
    content = await resp.read()

    elapsed = getattr(resp, "elapsed", timedelta())

    history: list[ResponseInterface] = (
        [
            AiohttpResponse(
                status_code=r.status,
                text=await r.text(),  # Obtendo o texto assíncrono
                content=await r.read(),  # Obtendo o conteúdo assíncrono
                url=str(r.url),
                headers=dict(r.headers),
                cookies={k: v.value for k, v in r.cookies.items()},
                encoding=r.get_encoding(),
                elapsed=getattr(r, "elapsed", timedelta()),
                history=[],  # Não há histórico para uma resposta anterior
            )
            for r in resp.history
        ]
        if resp.history
        else []
    )

    response = AiohttpResponse(
        status_code=resp.status,
        text=text,
        content=content,
        url=str(resp.url),
        headers=dict(resp.headers),
        cookies={k: v.value for k, v in resp.cookies.items()},
        encoding=resp.get_encoding(),
        elapsed=elapsed,
        history=history,
    )
    return ResponseProxy(response)


@dataclass
class AioHttpAdapter(AsyncHTTPRequest):
    session: Optional[aiohttp.ClientSession] = None
    verify_ssl: bool = True

    async def init_session(self) -> None:
        if not self.session or self.session.closed:
            connector = aiohttp.TCPConnector(ssl=self.verify_ssl)
            self.session = aiohttp.ClientSession(connector=connector)

    async def close_session(self) -> None:
        if self.session and not self.session.closed:
            await self.session.close()
            self.session = None

    async def request(self, config: HTTPRequestConfig) -> ResponseInterface:
        config.validate()

        if config.options.verify != self.verify_ssl:
            await self.close_session()

            self.verify_ssl = config.options.verify
            connector = aiohttp.TCPConnector(ssl=self.verify_ssl)
            self.session = aiohttp.ClientSession(connector=connector)

        if not self.session or self.session.closed:
            await self.init_session()

        request_kwargs = config.options.dump(
            exclude_none=True, convert_cookies_to_dict=True
        )

        request_kwargs.pop("verify", None)

        request_kwargs["timeout"] = config.options.timeout or aiohttp.ClientTimeout(
            total=config.options.timeout
        )

        async with self.session.request(  # type: ignore
            method=config.method, url=config.url, **request_kwargs
        ) as resp:
            return await make_response(resp)

    async def requests(  # type: ignore
        self, configs: list[HTTPRequestConfig], max: int
    ) -> AsyncGenerator[list[ResponseInterface], None]:  # type: ignore
        for i in range(0, len(configs), max):
            chunk = configs[i : i + max]
            tasks = [self.request(cfg) for cfg in chunk]
            results = await asyncio.gather(*tasks)
            yield results
