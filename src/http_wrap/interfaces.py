from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import timedelta
from logging import Logger, LogRecord
from types import TracebackType
from typing import (
    Any,
    AsyncContextManager,
    Awaitable,
    Callable,
    ContextManager,
    List,
    Literal,
    Mapping,
    Optional,
    Protocol,
    Sequence,
    Tuple,
    Type,
    TypeVar,
    Union,
    get_args,
    runtime_checkable,
)

# ----------- URL ----------------


@runtime_checkable
class WrapURL(Protocol):
    def __str__(self) -> str: ...
    @property
    def scheme(self) -> str: ...
    @property
    def username(self) -> Optional[str]: ...
    @property
    def password(self) -> Optional[str]: ...
    @property
    def userinfo(self) -> bytes: ...
    @property
    def host(self) -> Optional[str]: ...
    @property
    def raw_host(self) -> Optional[bytes]: ...
    @property
    def port(self) -> Optional[int]: ...
    @property
    def netloc(self) -> bytes: ...
    @property
    def path(self) -> str: ...
    @property
    def raw_path(self) -> bytes: ...
    @property
    def query(self) -> bytes: ...
    @property
    def fragment(self) -> str: ...


# -------------- Response -----------------------------


class WrapResponse(Protocol):
    @property
    def status_code(self) -> int: ...
    @property
    def status(self) -> int: ...
    @property
    def url(self) -> str: ...
    @property
    def headers(self) -> Mapping[str, str]: ...
    @property
    def raw_headers(self) -> Mapping[str, str]: ...
    @property
    def cookies(self) -> Mapping[str, str]: ...
    @property
    def encoding(self) -> str: ...
    @property
    def elapsed(self) -> timedelta: ...
    @property
    def history(self) -> list["WrapResponse"]: ...
    @property
    def links(self) -> Mapping[str, str]: ...
    @property
    def ok(self) -> bool: ...
    @property
    def is_informational(self) -> bool: ...
    @property
    def is_success(self) -> bool: ...
    @property
    def is_error(self) -> bool: ...
    @property
    def is_client_error(self) -> bool: ...
    @property
    def is_server_error(self) -> bool: ...
    @property
    def is_redirect(self) -> bool: ...
    @property
    def is_permanent_redirect(self) -> bool: ...
    @property
    def has_redirect_location(self) -> bool: ...
    @property
    def reason(self) -> str: ...
    @property
    def reason_phrase(self) -> str: ...
    @property
    def original_url(self) -> str: ...
    @property
    def final_url(self) -> str: ...
    @property
    def host(self) -> str: ...

    def json(self) -> Union[Mapping[str, Any], Awaitable[Mapping[str, Any]]]: ...

    def raise_for_status(self) -> Any: ...
    def __str__(self) -> str: ...


@runtime_checkable
class WrapSyncResponse(WrapResponse, Protocol):
    @property
    def text(self) -> str: ...
    @property
    def content(self) -> bytes: ...


@runtime_checkable
class WrapAsyncResponse(WrapResponse, Protocol):
    def text(self) -> Awaitable[str]: ...
    def content(self) -> Awaitable[bytes]: ...


HTTPWrapResponse = Union[WrapSyncResponse, WrapAsyncResponse]

# ------------ Session and Client ----------------


httpmethod = Literal["get", "post", "put", "patch", "delete", "head", "options"]
ALLOWED_METHODS = tuple(get_args(httpmethod))


class HTTPWrapClient(Protocol):

    def request(
        self, method: httpmethod, url: Union[str, WrapURL], *args: Any, **kwargs: Any
    ) -> HTTPWrapResponse: ...

    def get(self, url: Union[str, WrapURL], **kwargs: Any) -> HTTPWrapResponse: ...

    def post(self, url: Union[str, WrapURL], **kwargs: Any) -> HTTPWrapResponse: ...

    def patch(self, url: Union[str, WrapURL], **kwargs: Any) -> HTTPWrapResponse: ...

    def put(self, url: Union[str, WrapURL], **kwargs: Any) -> HTTPWrapResponse: ...

    def head(self, url: Union[str, WrapURL], **kwargs: Any) -> HTTPWrapResponse: ...

    def delete(self, url: Union[str, WrapURL], **kwargs: Any) -> HTTPWrapResponse: ...

    def close(self) -> None: ...

    def __enter__(self) -> "HTTPWrapClient": ...

    def __exit__(
        self,
        exc_type: Optional[Type[BaseException]],
        exc_val: Optional[BaseException],
        exc_tb: Optional[TracebackType],
    ) -> Optional[bool]: ...
    async def __aenter__(self) -> "HTTPWrapClient": ...
    async def __aexit__(
        self,
        exc_type: Optional[Type[BaseException]],
        exc_val: Optional[BaseException],
        exc_tb: Optional[TracebackType],
    ) -> Optional[bool]: ...


HTTPWrapSession = Union[
    ContextManager[HTTPWrapClient],
    AsyncContextManager[HTTPWrapClient],
]

T_contra = TypeVar("T_contra", contravariant=True)
T_co = TypeVar("T_co", covariant=True)


@runtime_checkable
class RunCheck(Protocol[T_contra]):
    def __call__(
        self,
        method: httpmethod,
        url: Union[str, WrapURL],
        args: Sequence[Any],
        kwargs: Mapping[str, Any],
        config: T_contra,
    ) -> Tuple[Sequence[Any], Mapping[str, Any]]: ...


@runtime_checkable
class HTTPWrapFactory(Protocol[T_co]):
    def __call__(
        self,
        backend_cls: HTTPWrapSession,
        configs: Optional[Any],
        run_check: RunCheck[T_co],
        validate_client: Callable[[HTTPWrapSession], None],
        response_proxy: Callable[[Any], WrapResponse],
        **kwargs: Any,
    ) -> HTTPWrapClient: ...
