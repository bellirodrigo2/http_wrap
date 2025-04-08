from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import timedelta
from typing import Any, Protocol, runtime_checkable

from http_wrap.security import Headers, RedirectPolicy, make_headers


@runtime_checkable
class ResponseInterface(Protocol):
    @property
    def status_code(self) -> int: ...
    @property
    def text(self) -> str: ...
    @property
    def content(self) -> bytes: ...
    @property
    def url(self) -> str: ...
    @property
    def headers(self) -> Mapping[str, str]: ...
    @property
    def cookies(self) -> Mapping[str, str]: ...
    def json(self) -> Mapping[str, Any]: ...
    @property
    def encoding(self) -> str: ...
    @property
    def elapsed(self) -> timedelta: ...
    @property
    def history(self) -> list["ResponseInterface"]: ...

    # @property
    # def reason(self) -> str: ...


@dataclass
class ResponseProxy(ResponseInterface):
    _response: Any = field(repr=False)

    def __post_init__(self) -> None:
        if not RedirectPolicy.is_enabled():
            return  # skip check if disabled

        original_url = (
            self._response.history[0].url
            if self._response.history
            else self._response.url
        )
        redirect_chain = [r.url for r in self._response.history] + [self._response.url]

        if not RedirectPolicy.is_safe(original_url, redirect_chain):
            raise ValueError(f"Insecure redirect detected: {redirect_chain}")

    @property
    def status_code(self) -> int:
        return self._response.status_code

    @property
    def text(self) -> str:
        return self._response.text

    @property
    def content(self) -> bytes:
        return self._response.content

    @property
    def url(self) -> str:
        return str(self._response.url)

    @property
    def headers(self) -> Headers:
        return Headers(dict(self._response.headers))
        # return make_headers(dict(self._response.headers))

    @property
    def cookies(self) -> Mapping[str, str]:
        return dict(self._response.cookies)

    def json(self) -> Mapping[str, Any]:
        return self._response.json()

    @property
    def encoding(self) -> str:
        return getattr(self._response, "encoding", "utf-8")

    @property
    def elapsed(self) -> timedelta:
        return getattr(self._response, "elapsed", timedelta(0))

    @property
    def history(self) -> list[ResponseInterface]:
        return getattr(self._response, "history", [])

    # Descomente se necessário
    # @property
    # def reason(self) -> str:
    #     return getattr(self._response, "reason", "")

    def __str__(self) -> str:
        return f"<ResponseProxy status={self.status_code}>"

    def __repr__(self) -> str:
        return self.__str__()
