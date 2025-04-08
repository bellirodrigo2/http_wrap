import ipaddress
import socket
from collections.abc import ItemsView, KeysView, Mapping, ValuesView
from dataclasses import dataclass, field
from typing import Any, Iterator, Optional
from urllib.parse import urlparse

from http_wrap.proxy import Handler, Proxy
from http_wrap.settings import get_settings

INTERNAL_DOMAINS = (".local", ".internal", ".lan")


def is_internal_address(host: str) -> bool:
    host = host.lower()
    if host == "localhost" or host.endswith(".local") or host.endswith(".internal"):
        return True

    try:
        ip = ipaddress.ip_address(socket.gethostbyname(host))
        return (
            ip.is_private
            or ip.is_loopback
            or ip.is_reserved
            or ip.is_multicast
            or ip.is_link_local
        )
    except Exception:
        return False


SENSITIVE_HEADERS = {"authorization", "cookie", "x-api-key"}


def is_redacted(header_name: str) -> bool:
    name = header_name.lower()
    settings = get_settings()

    if name in (h.lower() for h in settings.redact_headers):
        return True

    if any(
        name.startswith(p.lower())
        for p in getattr(settings, "redact_headers_startswith", [])
    ):
        return True

    if any(
        name.endswith(s.lower())
        for s in getattr(settings, "redact_headers_endswith", [])
    ):
        return True

    return False


@dataclass
class Headers(Mapping):
    _headers: dict[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self._headers = {k.lower(): str(v) for k, v in self._headers.items()}

    def __getitem__(self, key: str) -> str:
        return self._headers[key.lower()]

    def __iter__(self) -> Iterator[str]:
        return iter(self._headers)

    def __len__(self) -> int:
        return len(self._headers)

    def __contains__(self, key: object) -> bool:
        return isinstance(key, str) and key.lower() in self._headers

    def get(self, key: str, default: Any = None) -> Any:
        k = key.lower()
        if is_redacted(k):
            return "<redacted>"
        return self._headers.get(k, default)

    def items(self) -> ItemsView[str, str]:
        return self._headers.items()

    def keys(self) -> KeysView[str]:
        return self._headers.keys()

    def values(self) -> ValuesView[str]:
        return self._headers.values()

    def raw(self) -> dict[str, str]:
        """Access raw lowercase headers."""
        return self._headers.copy()

    def safe_repr(self) -> dict[str, str]:
        return {
            k: "<redacted>" if is_redacted(k) else v for k, v in self._headers.items()
        }

    def __str__(self) -> str:
        return str(self.safe_repr())

    def __repr__(self) -> str:
        return f"<Headers {self.safe_repr()}>"


class RedirectPolicy:
    _enabled: bool = False
    _allow_cross_domain: bool = False
    _trusted_domains: set[str] = set()

    @classmethod
    def set_redirect_policy(
        cls,
        *,
        enabled: bool = True,
        allow_cross_domain: bool = False,
        trusted_domains: set[str] = set([]),
    ) -> None:
        cls._enabled = enabled
        cls._allow_cross_domain = allow_cross_domain
        cls._trusted_domains = set(trusted_domains or [])

    @classmethod
    def is_enabled(cls) -> bool:
        return cls._enabled

    @classmethod
    def is_safe(cls, original_url: str, redirected_urls: list[str]) -> bool:
        origin_host = urlparse(original_url).hostname
        for redirected in redirected_urls:
            target_host = urlparse(redirected).hostname
            if origin_host == target_host:
                continue
            if cls._allow_cross_domain or target_host in cls._trusted_domains:
                continue
            return False
        return True


def make_headers(headers: dict[str, str]) -> Proxy[dict[str, str]]:
    sanitized = {k.lower(): str(v) for k, v in headers.items()}

    def proxy_getitem(obj: dict[str, str], key: str) -> str:
        return obj[key.lower()]

    def proxy_call_get(obj: dict[str, str], key: str, default: Any) -> Optional[str]:
        k = key.lower()
        if is_redacted(k):
            return "<redacted>"
        return obj.get(key, default)

    def proxy_call_saferepr(obj: dict[str, str]) -> dict[str, str]:
        return {k: "<redacted>" if is_redacted(k) else v for k, v in obj.items()}

    def proxy_get_raw(obj: dict[str, str]) -> dict[str, str]:
        return obj.copy()

    def proxy_str(obj: dict[str, str]) -> str:
        return str(proxy_call_saferepr(obj))

    def proxy_repr(obj: dict[str, str]) -> str:
        return f"<Headers {proxy_call_saferepr(obj)}>"

    handler: Handler[dict[str, str]] = Handler(
        getitem=proxy_getitem,
        get={"raw": proxy_get_raw},
        call={"get": proxy_call_get, "safe_repr": proxy_call_saferepr},
        str=proxy_str,
        repr=proxy_repr,
    )

    return Proxy.wrap(sanitized, handler)  # type: ignore

    # def __contains__(self, key: object) -> bool:
    # return isinstance(key, str) and key.lower() in self._headers
