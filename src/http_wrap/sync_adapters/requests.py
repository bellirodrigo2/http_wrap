from dataclasses import dataclass, field
from typing import Iterable

import requests

from http_wrap.request import HTTPRequestConfig, SyncHTTPRequest
from http_wrap.response import ResponseInterface, ResponseProxy


@dataclass
class RequestsAdapter(SyncHTTPRequest):
    session: requests.Session = field(default_factory=requests.Session)

    def request(self, config: HTTPRequestConfig) -> ResponseInterface:
        config.validate()

        request_kwargs = config.options.dump(
            exclude_none=True, convert_cookies_to_dict=True
        )

        response = self.session.request(
            method=config.method, url=config.url, **request_kwargs
        )
        return ResponseProxy(response)

    def requests(
        self, configs: list[HTTPRequestConfig], max: int = 1
    ) -> Iterable[ResponseInterface]:
        for config in configs:
            yield self.request(config)
