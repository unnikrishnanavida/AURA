"""Provider error taxonomy.

Raised at the canonical provider boundary so callers (the manager) can
distinguish timeout / unavailability / malformed-response failures without
catching raw network exceptions. These are *fallback* triggers, never
request-crashing errors: the reasoning pipeline stays deterministic when a
provider fails.
"""

from __future__ import annotations

__all__ = [
    "MalformedProviderResponse",
    "ProviderError",
    "ProviderPolicyError",
    "ProviderTimeoutError",
    "ProviderUnavailableError",
]


class ProviderError(RuntimeError):
    """Base class for provider-boundary failures."""


class ProviderTimeoutError(ProviderError):
    """The provider did not respond within its configured timeout."""


class ProviderUnavailableError(ProviderError):
    """The provider endpoint refused, failed, or could not be reached."""


class MalformedProviderResponse(ProviderError):
    """The provider returned a response that does not match the contract."""


class ProviderPolicyError(ProviderError):
    """Selection was impossible because policy constraints excluded all providers."""