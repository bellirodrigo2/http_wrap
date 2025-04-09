# httpwrap/settings.py

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class HttpLibSettings:
    default_timeout: float = 5.0
    allow_internal_access: bool = False
    redirect_enabled: bool = True
    allow_cross_domain: bool = False
    trusted_domains: list[str] = field(default_factory=list)

    # Redaction patterns
    redact_headers: list[str] = field(
        default_factory=lambda: ["Authorization", "Proxy-Authorization"]
    )
    redact_headers_startswith: list[str] = field(default_factory=list)
    redact_headers_endswith: list[str] = field(default_factory=list)
    redact_headers_contain: list[str] = field(default_factory=list)


# Internal singleton instance
_settings = HttpLibSettings()


def get_settings() -> HttpLibSettings:
    """
    Returns the current global settings instance.
    """
    return _settings


def configure(
    *,
    default_timeout: Optional[float] = None,
    allow_internal_access: Optional[bool] = None,
    redirect_enabled: Optional[bool] = None,
    allow_cross_domain: Optional[bool] = None,
    trusted_domains: Optional[list[str]] = None,
    redact_headers: Optional[list[str]] = None,
    redact_headers_startswith: Optional[list[str]] = None,
    redact_headers_endswith: Optional[list[str]] = None,
    redact_headers_contain: Optional[list[str]] = None,
) -> None:
    if default_timeout is not None:
        _settings.default_timeout = default_timeout
    if allow_internal_access is not None:
        _settings.allow_internal_access = allow_internal_access
    if redirect_enabled is not None:
        _settings.redirect_enabled = redirect_enabled
    if allow_cross_domain is not None:
        _settings.allow_cross_domain = allow_cross_domain
    if trusted_domains is not None:
        _settings.trusted_domains = trusted_domains
    if redact_headers is not None:
        _settings.redact_headers = redact_headers
    if redact_headers_startswith is not None:
        _settings.redact_headers_startswith = redact_headers_startswith
    if redact_headers_endswith is not None:
        _settings.redact_headers_endswith = redact_headers_endswith
    if redact_headers_contain is not None:
        _settings.redact_headers_contain = redact_headers_contain


def reset_settings() -> None:
    """
    Resets all global settings to their default values.
    Useful in testing environments.
    """
    global _settings
    _settings = HttpLibSettings()
