from collections.abc import AsyncGenerator, Iterable, Mapping
from dataclasses import asdict, dataclass, field
from typing import Any, Literal, Optional, Protocol, Union, cast, get_args
from urllib.parse import urlparse

from http_wrap.response import ResponseInterface
from http_wrap.security import Headers, is_internal_address
from http_wrap.settings import get_settings

httpmethod = Literal["get", "post", "put", "patch", "delete", "head"]

ALLOWED_METHODS = set(get_args(httpmethod))

METHODS_WITH_BODY = {"post", "put", "patch"}
METHODS_WITH_PARAMS = {"get", "delete", "head"}
METHODS_WITH_REDIRECTS = {"get", "options"}


@dataclass
class HTTPRequestOptions:
    headers: Optional[Mapping[str, str]] = None
    params: Optional[Mapping[str, str]] = None
    json: Optional[dict[str, Any]] = None
    timeout: Optional[float] = None
    allow_redirects: Optional[bool] = None
    verify: bool = True
    cookies: Optional[Mapping[str, str]] = None

    def __post_init__(self) -> None:
        if self.json is not None and not isinstance(self.json, dict):
            raise TypeError("body must be a mapping")

        for attr_name in ("headers", "params", "cookies"):
            val = getattr(self, attr_name)
            if val is not None:
                if not isinstance(val, Mapping):
                    raise TypeError(
                        f"{attr_name} must be a mapping, got {type(val).__name__}"
                    )
                if not all(isinstance(k, str) for k in val.keys()):
                    raise TypeError(f"All keys in {attr_name} must be strings")

        if self.timeout is None:
            self.timeout = get_settings().default_timeout

        if self.timeout is not None and self.timeout <= 0:
            raise ValueError("timeout must be a positive number")

        if self.headers is not None:
            self.headers = Headers(dict(self.headers))

        self.params = dict(self.params) if self.params is not None else None
        self.cookies = dict(self.cookies) if self.cookies is not None else None

    def dump(
        self, exclude_none: bool = False, convert_cookies_to_dict: bool = False
    ) -> dict[str, Any]:
        data = asdict(self)

        if convert_cookies_to_dict and data.get("cookies") is not None:
            data["cookies"] = dict(data["cookies"])

        if exclude_none:
            data = {k: v for k, v in data.items() if v is not None}

        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "HTTPRequestOptions":
        known_fields = {f.name for f in cls.__dataclass_fields__.values()}
        unknown_keys = set(data) - known_fields
        if unknown_keys:
            raise ValueError(f"Unknown option keys: {unknown_keys}")
        return cls(**data)


@dataclass
class HTTPRequestConfig:
    method: str
    url: str
    options: HTTPRequestOptions = field(default_factory=HTTPRequestOptions)
    allow_internal: bool = False

    def __post_init__(self) -> None:
        if not isinstance(self.url, str) or not self.url:
            raise ValueError("url must be a non-empty string")

        if not isinstance(self.method, str) or not self.method:
            raise ValueError("method must be a non-empty string")

        self.method = self.method.lower()
        if self.method not in ALLOWED_METHODS:
            raise ValueError(f"Unsupported HTTP method: {self.method}")

        if not isinstance(self.options, HTTPRequestOptions):
            raise TypeError("options must be of type HTTPRequestOptions")

        if not get_settings().allow_internal_access:
            if self.allow_internal:
                raise ValueError(
                    "Internal IP access is disabled. "
                    "Use settings.configure(allow_internal_access=True) to enable it."
                )
            self.allow_internal = False

        if self.options.allow_redirects is None:
            self.options.allow_redirects = self.method in METHODS_WITH_REDIRECTS

        self.validate()

    def _validate_url(self, allowed_schemes: set[str] = {"http", "https"}) -> None:
        parsed = urlparse(self.url)

        if not parsed.scheme or parsed.scheme not in allowed_schemes:
            raise ValueError(f"Invalid URL scheme: {parsed.scheme}")

        if not parsed.netloc:
            raise ValueError("URL must have a valid hostname")

        if not self.allow_internal and is_internal_address(parsed.hostname):
            raise ValueError(
                f"Internal address '{parsed.hostname}' is not allowed (set allow_internal=True to bypass)"
            )

    def validate(self) -> None:
        has_body = self.method in METHODS_WITH_BODY
        has_params = self.method in METHODS_WITH_PARAMS
        method_upper = self.method.upper()

        self._validate_url()

        if has_body and self.options.json is None:
            raise ValueError(
                f"{method_upper} request requires a body in `options.json`"
            )

        if not has_body and self.options.json is not None:
            raise ValueError(
                f"{method_upper} request does not support a body (use `params` if needed)"
            )

        if has_params and self.options.params is not None:
            if not isinstance(self.options.params, dict):
                raise TypeError(f"{method_upper} request expects params to be a dict")


class SyncHTTPRequest(Protocol):
    def request(self, config: HTTPRequestConfig) -> ResponseInterface: ...

    def requests(
        self, configs: list[HTTPRequestConfig], max: int
    ) -> Iterable[ResponseInterface]: ...


class AsyncHTTPRequest(Protocol):
    async def init_session(self) -> None: ...
    async def close_session(self) -> None: ...

    async def request(self, config: HTTPRequestConfig) -> ResponseInterface: ...

    async def requests(
        self, configs: list[HTTPRequestConfig], max: int
    ) -> AsyncGenerator[list[ResponseInterface], None]: ...


HTTPRequest = Union[SyncHTTPRequest, AsyncHTTPRequest]
