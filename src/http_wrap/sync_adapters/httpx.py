from dataclasses import dataclass, field
from http_wrap.request import HTTPRequestConfig, HTTPRequestOptions, SyncHTTPRequest
from http_wrap.response import ResponseInterface
import httpx
from typing import Iterable

@dataclass
class HttpxAdapter(SyncHTTPRequest):
    client: httpx.Client = field(default_factory=httpx.Client)

    def request(self, config: HTTPRequestConfig):

        config.validate()

        self.client.verify = config.options.verify_ssl if config.options.verify_ssl is not None else True

        response = self.client.request(
            method=config.method.lower(),
            url=config.url,
            headers=config.options.headers,
            params=config.options.params,
            json=config.options.body,
            timeout=config.options.timeout,
            follow_redirects=config.options.allow_redirects,
            cookies=config.options.cookies
        )
        return response

    def requests(
        self, configs: list[HTTPRequestConfig], max: int = 1
    ) -> Iterable[ResponseInterface]:
        for config in configs:
            yield self.request(config)