import ipaddress
import socket

INTERNAL_DOMAINS = (".local", ".internal", ".lan")


def is_internal_address(host: str) -> bool:
    try:
        ip = ipaddress.ip_address(socket.gethostbyname(host))
        return ip.is_private or ip.is_loopback
    except Exception:
        pass

    # Check internal domains
    return any(host.endswith(suffix) for suffix in INTERNAL_DOMAINS)


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
