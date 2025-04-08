from dataclasses import dataclass
from typing import Iterable, Optional

import httpx

from http_wrap.request import HTTPRequestConfig, SyncHTTPRequest
from http_wrap.response import ResponseInterface, ResponseProxy


@dataclass
class HttpxAdapter(SyncHTTPRequest):
    session: Optional[httpx.Client] = None
    verify_ssl: bool = True

    def __post_init__(self) -> None:
        if not self.session or getattr(self.session, "closed", True):
            self.session = httpx.Client(verify=self.verify_ssl)

    def request(self, config: HTTPRequestConfig) -> ResponseInterface:
        config.validate()

        if config.options.verify != self.verify_ssl:
            if self.session and not getattr(self.session, "closed", True):
                self.session.close()
            self.session = httpx.Client(verify=config.options.verify)
            self.verify_ssl = config.options.verify

        request_kwargs = config.options.dump(
            exclude_none=True, convert_cookies_to_dict=True
        )

        request_kwargs["follow_redirects"] = request_kwargs.pop("allow_redirects", True)
        request_kwargs.pop("verify", None)

        response = self.session.request(
            method=config.method, url=config.url, **request_kwargs
        )  # type: ignore

        return ResponseProxy(response)

    def requests(
        self, configs: list[HTTPRequestConfig], max: int = 1
    ) -> Iterable[ResponseInterface]:
        for config in configs:
            yield self.request(config)
