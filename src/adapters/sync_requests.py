from dataclasses import dataclass, field
from typing import Iterable

import requests

from src.request import HTTPRequestConfig, HTTPRequestOptions, SyncHTTPRequest
from src.response import ResponseInterface


@dataclass
class RequestsAdapter(SyncHTTPRequest):
    session: requests.Session = field(default_factory=requests.Session)

    def request(self, config: HTTPRequestConfig) -> ResponseInterface:
        config.validate()  # Validações específicas (método + opções)

        method = config.method.lower()
        url = config.url
        opts = config.options or HTTPRequestOptions()

        response = self.session.request(
            method=method,
            url=url,
            headers=opts.headers,
            params=opts.params,
            json=opts.body,
            timeout=opts.timeout,
            allow_redirects=(
                opts.allow_redirects if opts.allow_redirects is not None else True
            ),
            verify=opts.verify_ssl if opts.verify_ssl is not None else True,
            cookies=dict(opts.cookies) if opts.cookies else None,
        )
        return response

    def requests(
        self, configs: list[HTTPRequestConfig], max: int = 1
    ) -> Iterable[ResponseInterface]:
        for config in configs:
            yield self.request(config)
