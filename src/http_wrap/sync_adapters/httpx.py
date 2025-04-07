from dataclasses import dataclass, field
from typing import Iterable

import httpx

from http_wrap.request import HTTPRequestConfig, SyncHTTPRequest
from http_wrap.response import ResponseInterface


@dataclass
class HttpxAdapter(SyncHTTPRequest):
    session: httpx.Client = field(default_factory=httpx.Client)

    def request(self, config: HTTPRequestConfig):

        config.validate()

        self.session.verify = config.options.verify

        request_kwargs = config.options.dump(
            exclude_none=True, convert_cookies_to_dict=True
        )

        request_kwargs["follow_redirects"] = request_kwargs.pop("allow_redirects", True)
        request_kwargs.pop("verify", None)

        response = self.session.request(
            method=config.method, url=config.url, **request_kwargs
        )

        return response

    def requests(
        self, configs: list[HTTPRequestConfig], max: int = 1
    ) -> Iterable[ResponseInterface]:
        for config in configs:
            yield self.request(config)
