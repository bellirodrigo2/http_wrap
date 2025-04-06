import asyncio
from collections.abc import AsyncGenerator
from dataclasses import dataclass, field
from datetime import timedelta
from typing import Any

import aiohttp

from src.http_wrap.request import (
    AsyncHTTPRequest,
    HTTPRequestConfig,
    HTTPRequestOptions,
)
from src.http_wrap.response import ResponseInterface



@dataclass(frozen=True)
class AiohttpResponse:
    status_code: int
    text: str
    content: bytes
    url: str
    headers: dict[str, str] = field(default_factory=dict)
    cookies: dict[str, str] = field(default_factory=dict)
    encoding: str = 'utf-8'
    elapsed: timedelta = field(default_factory=timedelta)
    history: list['ResponseInterface'] = field(default_factory=list)
    reason: str = ''

    def json(self) -> dict[str, Any]:
        import json
        try:
            return json.loads(self.text)
        except json.JSONDecodeError:
            return {}

async def make_response(resp: aiohttp.ClientResponse) -> ResponseInterface:
    text = await resp.text()
    content = await resp.read()

    elapsed = getattr(resp, 'elapsed', timedelta())
    
    history = [
        AiohttpResponse(
            status_code=r.status,
            text=await r.text(),  # Obtendo o texto assíncrono
            content=await r.read(),  # Obtendo o conteúdo assíncrono
            url=str(r.url),
            headers=dict(r.headers),
            cookies=dict(r.cookies),
            encoding=r.get_encoding(),
            elapsed=getattr(r, 'elapsed', timedelta()),
            history=[],  # Não há histórico para uma resposta anterior
            reason=r.reason
        )
        for r in resp.history
    ] if resp.history else []

    return AiohttpResponse(
        status_code=resp.status,
        text=text,
        content=content,
        url=str(resp.url),
        headers=dict(resp.headers),
        cookies=dict(resp.cookies),
        encoding=resp.get_encoding(),
        elapsed=elapsed,
        history=history,
        reason=resp.reason
    )


@dataclass
class AioHttpAdapter(AsyncHTTPRequest):
    session: aiohttp.ClientSession | None = None

    async def init_session(self, verify_ssl: bool = True) -> None:
        if not self.session or self.session.closed:
            connector = aiohttp.TCPConnector(ssl=verify_ssl)
            self.session = aiohttp.ClientSession(connector=connector)

    async def close_session(self) -> None:
        if self.session and not self.session.closed:
            await self.session.close()
            self.session = None

    async def request(self, config: HTTPRequestConfig) -> ResponseInterface:
        method = config.method.lower()
        url = config.url
        opts: HTTPRequestOptions = config.options or HTTPRequestOptions()

        if not self.session or self.session.closed:
            raise Exception("Session is Closed")

        timeout = (
            aiohttp.ClientTimeout(total=opts.timeout)
            if opts.timeout is not None
            else None
        )

        async with self.session.request(
            method,
            url,
            headers=opts.headers,
            params=opts.params,
            json=opts.body,
            timeout=timeout,
            allow_redirects=(
                opts.allow_redirects if opts.allow_redirects is not None else True
            ),
            # verify=opts.verify_ssl if opts.verify_ssl is not None else True,
            cookies=dict(opts.cookies) if opts.cookies else None,
        ) as resp:
            return await make_response(resp)

    async def requests(
        self, configs: list[HTTPRequestConfig], max: int
    ) -> AsyncGenerator[list[ResponseInterface], None]:  # type: ignore
        for i in range(0, len(configs), max):
            chunk = configs[i : i + max]
            tasks = [self.request(cfg) for cfg in chunk]
            results = await asyncio.gather(*tasks)
            yield results
