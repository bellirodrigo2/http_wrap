# --------------------- Config --------------

from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import (
    Any,
    Callable,
    List,
    Optional,
    Protocol,
    Sequence,
    Tuple,
    Union,
    runtime_checkable,
)

from http_wrap.hooks import check_consistency, raise_on_internal_address, validate_url
from http_wrap.interfaces import ALLOWED_METHODS, WrapURL, httpmethod

RedactHeaders = Tuple[List[str], List[str], List[str], List[str]]


@runtime_checkable
class LoggerProtocol(Protocol):
    def debug(self, msg: Any, *args: Any, **kwargs: Any) -> None: ...
    def info(self, msg: Any, *args: Any, **kwargs: Any) -> None: ...
    def warning(self, msg: Any, *args: Any, **kwargs: Any) -> None: ...
    def error(self, msg: Any, *args: Any, **kwargs: Any) -> None: ...
    def exception(
        self, msg: Any, *args: Any, exc_info: Any = ..., **kwargs: Any
    ) -> None: ...
    def critical(self, msg: Any, *args: Any, **kwargs: Any) -> None: ...
    def log(self, level: int, msg: Any, *args: Any, **kwargs: Any) -> None: ...
    def isEnabledFor(self, level: int) -> bool: ...


class NullLogger(LoggerProtocol):
    def __getattr__(self, name: str) -> Callable[..., Any]:
        def noop(*args: Any, **kwargs: Any) -> None:
            pass

        return noop


@dataclass(frozen=True)
class HTTPWrapConfig:
    allow_internal: bool = field(default=False)
    validate_url: bool = field(default=True)
    check_request_consistency: bool = field(default=True)
    proxy_response: bool = field(default=True)
    sanitize_auth: bool = field(default=True)  # FALTA

    max_redirects: int = field(default=20)  # FALTA
    default_timeout: float = field(default=5)  # FALTA

    allowed_methods: Sequence[httpmethod] = field(default=ALLOWED_METHODS)
    sanitize_resp_header: RedactHeaders = field(default=([], [], [], []))
    trusted_domains: Optional[Sequence[str]] = None  # FALTA

    logger: LoggerProtocol = field(default_factory=NullLogger)
    default_cert: Optional[List[str]] = field(default_factory=list)  # FALTA


def run_check_config(
    method: httpmethod,
    url: Union[str, WrapURL],
    args: Sequence[Any],
    kwargs: Mapping[str, Any],
    config: HTTPWrapConfig,
) -> Tuple[Sequence[Any], Mapping[str, Any]]:

    if not config.allow_internal:
        raise_on_internal_address(url)
    if config.validate_url:
        validate_url(url)

    check_consistency(
        method=method,
        params=kwargs.get("params", None),
        json=kwargs.get("json", None),
        data=kwargs.get("data", None),
        files=kwargs.get("file", None),
        allowed_methods=config.allowed_methods,
        redirects=config.max_redirects > 0,
    )
    return args, kwargs
