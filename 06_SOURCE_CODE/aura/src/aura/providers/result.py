"""Canonical provider outcome, state and capability vocabulary.

Phase 2 of the provider slice. One place that answers, without guessing:

- **What happened** when a provider was consulted (:class:`ProviderStatus`) --
  a closed taxonomy, never a bare ``None`` that hides the difference between
  "no provider configured", "provider down", "timed out", and "not allowed".
- **What state a provider is in** (:class:`ProviderState`) -- REGISTERED,
  CONFIGURED, AVAILABLE, AUTHORIZED, SUPPORTED and SELECTED are distinct facts
  about different subjects, and a registry entry alone is not permission.
- **What AURA needs from a provider** (:class:`ProviderCapability`) -- what an
  adapter can support is discovered from its profile, never assumed.

This module holds data only. It performs no I/O, so both the provider runtime
and the API layer can depend on it without importing each other.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any


class ProviderStatus(StrEnum):
    """The closed outcome taxonomy for one provider consultation."""

    #: The provider produced output.
    OK = "ok"
    #: No provider is configured at all (the default AURA deployment).
    NOT_CONFIGURED = "not_configured"
    #: Providers exist and match, but none cleared policy/privacy/authorization.
    UNAUTHORIZED = "unauthorized"
    #: A provider matched but its health probe says it cannot be reached.
    UNAVAILABLE = "unavailable"
    #: The named model is not present on an otherwise reachable endpoint.
    MODEL_UNAVAILABLE = "model_unavailable"
    #: The provider rejected our credentials.
    AUTHENTICATION_FAILED = "authentication_failed"
    #: The provider refused for authorization/permission reasons.
    FORBIDDEN = "forbidden"
    #: The provider did not answer within its bounded timeout.
    TIMEOUT = "timeout"
    #: The caller cancelled before or during the call.
    CANCELLED = "cancelled"
    #: The provider throttled us.
    RATE_LIMITED = "rate_limited"
    #: A transient provider-side failure (5xx / connection reset).
    TRANSIENT_FAILURE = "transient_failure"
    #: The response did not match the provider contract.
    MALFORMED_RESPONSE = "malformed_response"
    #: The provider cannot do what was asked (no such capability).
    UNSUPPORTED_CAPABILITY = "unsupported_capability"
    #: A configured budget or resource ceiling blocked the call.
    BUDGET_EXCEEDED = "budget_exceeded"


#: Statuses where retrying the same request later is reasonable. Exposed so the
#: API layer can tell a client "try again" without re-deriving the policy.
RETRYABLE_STATUSES: frozenset[ProviderStatus] = frozenset(
    {
        ProviderStatus.TIMEOUT,
        ProviderStatus.RATE_LIMITED,
        ProviderStatus.TRANSIENT_FAILURE,
        ProviderStatus.UNAVAILABLE,
    }
)


class ProviderState(StrEnum):
    """Lifecycle states, per subject.

    REGISTERED/CONFIGURED describe the adapter; AVAILABLE describes the remote
    endpoint; AUTHORIZED describes the caller; SUPPORTED describes the model's
    declared capabilities; SELECTED is a decision this process made.
    """

    REGISTERED = "registered"
    CONFIGURED = "configured"
    AVAILABLE = "available"
    AUTHORIZED = "authorized"
    SUPPORTED = "supported"
    SELECTED = "selected"


class ProviderCapability(StrEnum):
    """Capabilities AURA asks for. Matched against adapter profiles."""

    SYNTHESIS = "reasoning.synthesis"
    GENERATION = "reasoning.generation"
    MULTI_STRATEGY = "reasoning.multi_strategy"
    DETERMINISTIC = "reasoning.deterministic"


@dataclass(frozen=True, slots=True)
class ProviderUsage:
    """Per-call usage reported by a provider, when the provider reports any."""

    prompt_tokens: int | None = None
    completion_tokens: int | None = None
    total_tokens: int | None = None
    calls: int = 0
    latency_ms: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "prompt_tokens": self.prompt_tokens,
            "completion_tokens": self.completion_tokens,
            "total_tokens": self.total_tokens,
            "calls": self.calls,
            "latency_ms": round(self.latency_ms, 3),
        }


@dataclass(frozen=True, slots=True)
class ProviderResult:
    """The structured outcome of one provider consultation.

    ``text`` is model output and is *never* implicitly trusted: AURA's reasoning
    layer decides what to do with it, and :attr:`verification` records that a
    model answer has not been verified merely by existing.
    """

    status: ProviderStatus
    text: str | None = None
    provider: str | None = None
    model: str | None = None
    local: bool | None = None
    finish_reason: str | None = None
    usage: ProviderUsage = field(default_factory=ProviderUsage)
    verification: str = "unverified"
    error: str | None = None
    retryable: bool = False
    #: When ``status`` is CANCELLED, the canonical pipeline stage at which the
    #: cancellation was observed: ``provider.dispatch`` (before the provider was
    #: called), ``provider.http`` (the in-flight HTTP request was interrupted),
    #: ``provider`` (inside the provider call) or ``provider.after_response``
    #: (after the response was received). ``None`` on any non-cancelled outcome.
    cancelled_stage: str | None = None

    @property
    def ok(self) -> bool:
        return self.status is ProviderStatus.OK and bool(self.text)

    def to_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "status": self.status.value,
            "provider": self.provider,
            "model": self.model,
            "local": self.local,
            "verification": self.verification,
            "retryable": self.retryable,
        }
        if self.finish_reason is not None:
            payload["finish_reason"] = self.finish_reason
        if self.cancelled_stage is not None:
            payload["cancelled_stage"] = self.cancelled_stage
        if self.error is not None:
            payload["error"] = self.error
        if self.usage.calls or self.usage.total_tokens is not None:
            payload["usage"] = self.usage.to_dict()
        return payload


@dataclass(frozen=True, slots=True)
class ProviderDescriptor:
    """What AURA can truthfully say about one provider right now.

    Deliberately reports *absence* as absence: a model that was never configured
    is ``None``, not an empty string, and no credential material ever appears.
    """

    name: str
    kind: str
    model: str | None
    local: bool
    configured: bool
    registered: bool
    available: bool | None
    privacy_approved: bool
    capabilities: tuple[str, ...]
    states: tuple[str, ...]
    timeout_seconds: float
    cost_per_call: float
    usage: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "kind": self.kind,
            "model": self.model,
            "local": self.local,
            "configured": self.configured,
            "registered": self.registered,
            "available": self.available,
            "privacy_approved": self.privacy_approved,
            "capabilities": list(self.capabilities),
            "states": list(self.states),
            "timeout_seconds": self.timeout_seconds,
            "cost_per_call": self.cost_per_call,
            "usage": dict(self.usage),
        }


__all__ = [
    "RETRYABLE_STATUSES",
    "ProviderCapability",
    "ProviderDescriptor",
    "ProviderResult",
    "ProviderState",
    "ProviderStatus",
    "ProviderUsage",
]