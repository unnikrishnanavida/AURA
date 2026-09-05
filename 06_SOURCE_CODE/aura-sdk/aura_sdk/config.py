"""SDK configuration.

``SdkConfig`` is validated at construction time so misconfiguration fails fast
in tests and at startup rather than halfway through a request. Secret material
(api key) is never dumped by ``to_public_dict``; the default is deny when the
key or token is empty.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum

from .errors import SdkConfigurationError

DEFAULT_ENDPOINT = "http://127.0.0.1:8765"
DEFAULT_TIMEOUT_SECONDS = 10.0
DEFAULT_RETRIES = 2


class TransportMode(StrEnum):
    LOCAL = "local"  # in-process canonical AURA runtime
    HTTP = "http"  # remote AURA API server


@dataclass(frozen=True, slots=True)
class RetryConfig:
    max_attempts: int = DEFAULT_RETRIES
    backoff_base_seconds: float = 0.25
    jitter_seconds: float = 0.05
    retryable_codes: tuple[str, ...] = ("sdk.timeout", "sdk.transport")

    def __post_init__(self) -> None:
        if self.max_attempts < 0:
            raise SdkConfigurationError("max_attempts must be >= 0")
        if self.backoff_base_seconds < 0:
            raise SdkConfigurationError("backoff_base_seconds must be >= 0")
        if self.jitter_seconds < 0:
            raise SdkConfigurationError("jitter_seconds must be >= 0")


@dataclass(frozen=True, slots=True)
class SdkConfig:
    mode: TransportMode = TransportMode.LOCAL
    endpoint: str = DEFAULT_ENDPOINT
    timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS
    retry: RetryConfig = field(default_factory=RetryConfig)
    api_key: str | None = None
    identity: str = "sdk-user"
    request_timeout_hint: str = "default"  # reserved: per-request override hooks

    def __post_init__(self) -> None:
        if self.timeout_seconds <= 0:
            raise SdkConfigurationError(f"timeout_seconds must be positive, got {self.timeout_seconds}")
        if self.mode is TransportMode.LOCAL and self.api_key is not None:
            raise SdkConfigurationError("api_key cannot be used in local mode (no remote boundary)")
        if not self.identity or not self.identity.strip():
            raise SdkConfigurationError("identity must be a non-empty string")
        if self.api_key is not None and len(self.api_key) < 8:
            raise SdkConfigurationError("api_key must be at least 8 characters (reject obvious test leaks)")

    def to_public_dict(self) -> dict[str, object]:
        """Public description with all secret material masked."""
        return {
            "mode": self.mode.value,
            "endpoint": self.endpoint,
            "timeout_seconds": self.timeout_seconds,
            "retry_max_attempts": self.retry.max_attempts,
            "identity": self.identity,
            "api_key_set": self.api_key is not None,
        }


__all__ = ["DEFAULT_ENDPOINT", "RetryConfig", "SdkConfig", "TransportMode"]