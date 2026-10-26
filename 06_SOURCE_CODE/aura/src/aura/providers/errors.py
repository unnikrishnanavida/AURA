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
    """Base class for provider-boundary failures.

    ``http_status`` is carried when the failure came from a real HTTP response so
    the manager can distinguish "your credentials were rejected" (401) from
    "the provider is down" (503) instead of reporting every non-200 alike.
    """

    def __init__(self, message: str, *, http_status: int | None = None) -> None:
        super().__init__(message)
        self.http_status = http_status


class ProviderTimeoutError(ProviderError):
    """The provider did not respond within its configured timeout."""


class ProviderUnavailableError(ProviderError):
    """The provider endpoint refused, failed, or could not be reached."""


class MalformedProviderResponse(ProviderError):
    """The provider returned a response that does not match the contract."""


class ProviderPolicyError(ProviderError):
    """Selection was impossible because policy constraints excluded all providers."""