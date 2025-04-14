import ipaddress
import socket
import stat
from dataclasses import dataclass, field
from http import HTTPStatus
from inspect import stack
from logging import Logger
from types import MethodType, TracebackType
from typing import (
    Any,
    Callable,
    Container,
    List,
    Literal,
    Mapping,
    Optional,
    Tuple,
    Union,
    get_args,
)
from urllib.parse import urlparse

import wrapt

from http_wrap.interfaces import HTTPWrapResponse, WrapURL

httpmethod = Literal["get", "post", "put", "patch", "delete", "head"]
ALLOWED_METHODS = get_args(httpmethod)

RedactHeaders = Tuple[List[str], List[str], List[str], List[str]]


@dataclass
class RequestConfig:
    allow_internal_access: bool = field(default=False)  # REQ
    sanitize_resp_header: Optional[RedactHeaders] = None  # RESP
    sanitize_auth: bool = field(default=True)
    exclude_none: bool = field(default=True)  # REQ
    validate_url: bool = field(default=True)  # REQ
    max_redirects: Optional[int] = field(default=0)  # REQ
    trusted_domains: Container[str] = field(default_factory=list[str])  # REQ
    default_timeout: Optional[float] = field(default=None)  # REQ
    default_cert: List[str] = field(default_factory=list)  # REQ
    allowed_methods: Container[httpmethod] = field(default=ALLOWED_METHODS)  # REQ
    # proxy_response: bool = field(default=True)
    error_mode: Literal["raise", "fix", "ignore"] = field(default="ignore")  # REQ
    nohooks: bool = field(default=True)  # REQ
    logging: Optional[Logger] = None
    check_request_consistency: bool = field(default=True)


def should_redact_header(
    name: str,
    match: list[str],
    startswith: list[str],
    endswith: list[str],
    contain: list[str],
) -> bool:
    name = name.lower()

    return (
        name in match
        or any(name.startswith(p) for p in startswith)
        or any(name.endswith(s) for s in endswith)
        or any(c in name for c in contain)
    )


def sanitize_headers(
    headers: dict[str, str],
    match: list[str],
    startswith: list[str],
    endswith: list[str],
    contain: list[str],
) -> dict[str, str]:
    return {
        k.lower(): (
            "<redacted>"
            if should_redact_header(k, match, startswith, endswith, contain)
            else v
        )
        for k, v in headers.items()
    }


class InternalAddressError(Exception):
    """Raised when an internal address is detected."""

    pass


def raise_on_internal_address(host: str) -> None:
    host = host.lower()

    # Heurística por nome
    if host == "localhost" or host.endswith(".local") or host.endswith(".internal"):
        raise InternalAddressError(f"Blocked internal address: {host!r}")

    try:
        ip_str = socket.gethostbyname(host)
        ip = ipaddress.ip_address(ip_str)

        if ip.is_private or ip.is_loopback or ip.is_link_local:
            raise InternalAddressError(
                f"Blocked internal IP address: {ip_str} ({host!r})"
            )

    except socket.gaierror as e:
        raise ValueError(f"Unable to resolve host: {host!r}") from e


def validate_url(url: str) -> None:
    if not isinstance(url, str) or not url.strip():
        raise ValueError("URL must be a non-empty string")

    parsed = urlparse(url)

    if not parsed.scheme:
        raise ValueError("URL must include a scheme (e.g. 'http' or 'https')")

    if not parsed.netloc or not parsed.hostname:
        raise ValueError("URL must include a valid hostname")


def extract_hostname(value: str) -> str:
    if "://" not in value:
        value = "http://" + value  # Apenas para o urlparse funcionar corretamente
    parsed = urlparse(value)
    return parsed.hostname or ""


from typing import Sequence, Union
from urllib.parse import urlparse


def extract_hostname(value: str) -> str:
    """
    Extrai o hostname de uma URL ou domínio.
    Adiciona http:// temporariamente caso não haja scheme, só para parsing.
    """
    if "://" not in value:
        value = "http://" + value  # Apenas para o urlparse funcionar corretamente
    parsed = urlparse(value)
    return parsed.hostname or ""


def is_allowed_domain(
    url: Union[str, "WrapURL"],
    allowed_domains: Sequence[str],
) -> bool:
    if isinstance(url, str):
        parsed = urlparse(url)
        host = parsed.hostname
    elif hasattr(url, "host"):
        host = url.host
    else:
        raise TypeError("Expected str or WrapURL-compliant object")
    if not host:
        return False
    host = host.lower()
    normalized_domains = [
        extract_hostname(domain).lower() for domain in allowed_domains
    ]
    return any(
        host == allowed or host.endswith("." + allowed)
        for allowed in normalized_domains
    )


def check_consistency(
    method: str,
    json: Optional[Any],
    params: Optional[Mapping[str, str]],
    data: Optional[Union[Mapping[str, Any], bytes]],
    files: Optional[Any],
    allowed_methods: Container[str],
    redirects: bool = True,
) -> None:

    METHODS_WITH_BODY = {"post", "put", "patch"}
    METHODS_WITH_PARAMS = {"get", "delete", "head"}
    METHODS_WITH_REDIRECTS = {"get", "options"}

    method = method.lower()

    if method not in allowed_methods:
        raise ValueError(f"Unsupported HTTP method: {method}")

    has_body = method in METHODS_WITH_BODY
    has_params = method in METHODS_WITH_PARAMS
    can_redirect = method in METHODS_WITH_REDIRECTS
    method_upper = method.upper()

    if has_body and json is None:
        raise ValueError(f"{method_upper} request requires a body in `options.json`")

    if not has_body and json is not None:
        raise ValueError(
            f"{method_upper} request does not support a body (use `params` if needed)"
        )

    if has_params and params is not None:
        if not isinstance(params, dict):
            raise TypeError(f"{method_upper} request expects params to be a dict")


def extract_host(url: Union[str, WrapURL]) -> str:
    return url.host if hasattr(url, "host") else getattr(url, "netloc", "")


def check_url(configs: HTTPWrapConfig, url: Union[str, WrapURL]) -> None:

    if not configs.allow_internal:
        raise_on_internal_address(url)
    if configs.validate_url:
        validate_url(url)

    if configs.trusted_domains and not is_allowed_domain(url, configs.trusted_domains):
        raise ValueError(f"URL {url} is not within trusted domains")


def validate_client(client: Any) -> None:
    if not hasattr(client, "__enter__") or not hasattr(client, "__exit__"):
        raise TypeError(
            f"{type(client).__name__} must support context manager (__enter__/__exit__)"
        )

    required_methods = ("request", *ALLOWED_METHODS)

    for method in required_methods:
        if not hasattr(client, method):
            raise TypeError(
                f"{type(client).__name__} is missing required method: {method}()"
            )

    if not callable(getattr(client, "request", None)):
        raise TypeError(f"{type(client).__name__}.request is not callable")


if __name__ == "__main__":

    ...
