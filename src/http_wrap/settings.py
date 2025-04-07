# httpwrap/settings.py

from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class HttpLibSettings:
    """
    Global settings for the httpwrap library.
    """

    default_timeout: float = 5.0  # Default request timeout in seconds
    allow_internal_access: bool = (
        False  # Allow access to internal/private addresses (e.g., localhost)
    )
    redirect_enabled: bool = True  # Enable or disable HTTP redirects
    allow_cross_domain: bool = False  # Allow redirects to a different domain
    trusted_domains: List[str] = field(
        default_factory=list
    )  # Domains allowed for redirection
    redact_headers: List[str] = field(
        default_factory=lambda: ["Authorization", "Proxy-Authorization"]
    )  # Headers to be sanitized


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
    trusted_domains: Optional[List[str]] = None,
    redact_headers: Optional[List[str]] = None,
) -> None:
    """
    Updates global settings for the library.

    All arguments are optional. Only provided values will be updated.

    Example:
        configure(default_timeout=10.0, allow_internal_access=True)

    Raises:
        ValueError: If an unknown configuration key is provided.
    """
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


def reset_settings() -> None:
    """
    Resets all global settings to their default values.
    Useful in testing environments.
    """
    global _settings
    _settings = HttpLibSettings()
