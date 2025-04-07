import ipaddress
import socket
from collections.abc import Mapping

# from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Any, Iterator

INTERNAL_DOMAINS = (".local", ".internal", ".lan")


def is_internal_address(host: str) -> bool:
    try:
        ip = ipaddress.ip_address(socket.gethostbyname(host))
        return ip.is_private or ip.is_loopback
    except Exception:
        pass

    # Check internal domains
    return any(host.endswith(suffix) for suffix in INTERNAL_DOMAINS)


# def is_internal_address(host: str) -> bool:
#     host = host.lower()
#     if host == "localhost" or host.endswith(".local") or host.endswith(".internal"):
#         return True

#     try:
#         ip = ipaddress.ip_address(socket.gethostbyname(host))
#         return (
#             ip.is_private
#             or ip.is_loopback
#             or ip.is_reserved
#             or ip.is_multicast
#             or ip.is_link_local
#         )
#     except Exception:
#         return False


SENSITIVE_HEADERS = {"authorization", "cookie", "x-api-key"}


@dataclass
class Headers(Mapping):
    _headers: dict[str, str] = field(default_factory=dict)

    def __post_init__(self):
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
        return self._headers.get(key.lower(), default)

    def items(self):
        return self._headers.items()

    def keys(self):
        return self._headers.keys()

    def values(self):
        return self._headers.values()

    def raw(self) -> dict[str, str]:
        """Access raw lowercase headers."""
        return self._headers.copy()

    def safe_repr(self) -> dict[str, str]:
        return {
            k: ("<redacted>" if k in SENSITIVE_HEADERS else v)
            for k, v in self._headers.items()
        }

    def __str__(self) -> str:
        return str(self.safe_repr())

    def __repr__(self) -> str:
        return f"<Headers {self.safe_repr()}>"
