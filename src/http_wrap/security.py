import ipaddress
import socket
from urllib.parse import urlparse

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

    if any(s in name for s in getattr(settings, "redact_headers_endswith", [])):
        return True

    return False


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


def sanitize_headers(headers: dict[str, str]) -> dict[str, str]:
    return {
        k.lower(): "<redacted>" if is_redacted(k) else v for k, v in headers.items()
    }
