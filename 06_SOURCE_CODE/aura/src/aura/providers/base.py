"""Provider contracts and profiles.

Defines the canonical provider contract (:class:`Provider`), the declarative
:class:`ProviderProfile`, the ONE :class:`ProviderRegistry` (profiles + runtime
instances), and the policy/usage primitives used by the manager.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from aura.foundation.errors import CapabilityError, NotFoundError


@dataclass(frozen=True, slots=True)
class ProviderProfile:
    """Declarative description of one model provider."""

    name: str
    kind: str  # "reasoning" | "embedding" | "planning"
    capabilities: tuple[str, ...] = ("reasoning.basic",)
    latency_ms: float = 100.0
    cost_per_call: float = 0.001
    reliability: float = 0.99
    local: bool = True
    privacy_approved: bool = True

    def supports(self, required: str | None) -> bool:
        if required is None:
            return True
        return required in self.capabilities


class Provider:
    """Canonical runtime provider contract.

    Subclasses implement :meth:`reason` (generation/reasoning) and may override
    :meth:`health`, and must set ``profile`` (instance or class attribute).
    """

    name: str = "provider"
    kind: str = "reasoning"
    timeout_seconds: float = 15.0
    profile: ProviderProfile | None = None
    #: The concrete model this adapter talks to, when it has one. Adapters that
    #: are not model-backed (the embedded reasoner) leave it as ``None`` -- the
    #: difference between "no model" and "a model we could name" is preserved.
    model: str | None = None

    def health(self) -> bool:
        """Return True when the provider is usable right now."""
        return True

    def reason(self, question: str, **kwargs: Any) -> Any:
        """Run one provider consultation and return its output.

        Adapters may accept an optional ``cancellation`` keyword -- a
        :class:`~aura.foundation.cancellation.CancellationToken` -- and use it
        to abort in-flight work (e.g. the HTTP transport closing the
        connection). Adapters that cannot interrupt honour the token by simply
        ignoring it; the manager still checks it before and after the call.
        """
        raise NotImplementedError


@dataclass(frozen=True, slots=True)
class ProviderPolicy:
    """Policy filter applied during provider selection (never bypassed)."""

    required_capability: str | None = "reasoning.synthesis"
    require_local: bool = False
    require_privacy_approved: bool = True
    cost_budget: float | None = None
    latency_budget_ms: float | None = None
    allow_fallback: bool = True


@dataclass
class ProviderUsage:
    """Aggregate usage/failure counters at the provider boundary."""

    calls: int = 0
    failures: int = 0
    timeouts: int = 0
    policy_rejections: int = 0
    total_latency_ms: float = 0.0
    by_provider: dict[str, int] = field(default_factory=dict)

    def note_provider(self, name: str) -> None:
        self.by_provider[name] = self.by_provider.get(name, 0) + 1

    def snapshot(self) -> dict[str, Any]:
        return {
            "calls": self.calls,
            "failures": self.failures,
            "timeouts": self.timeouts,
            "policy_rejections": self.policy_rejections,
            "total_latency_ms": round(self.total_latency_ms, 3),
            "by_provider": dict(self.by_provider),
        }


class ProviderRegistry:
    """The single registry of provider profiles AND runtime instances."""

    def __init__(self) -> None:
        self._providers: dict[str, ProviderProfile] = {}
        self._instances: dict[str, Provider] = {}
        self._default: str | None = None

    def register(self, profile: ProviderProfile) -> None:
        self._providers[profile.name] = profile

    def register_instance(self, provider: Provider, profile: ProviderProfile | None = None) -> None:
        """Register a runtime instance together with its profile."""
        resolved = profile or getattr(provider, "profile", None)
        if resolved is None:
            raise ValueError(f"provider {provider!r} has no profile; pass one explicitly")
        self._providers[resolved.name] = resolved
        self._instances[resolved.name] = provider
        if self._default is None:
            self._default = resolved.name

    def set_default(self, name: str) -> None:
        if name not in self._providers:
            raise NotFoundError(f"provider not registered: {name}")
        self._default = name

    @property
    def default(self) -> str | None:
        return self._default

    def get(self, name: str) -> ProviderProfile:
        if name not in self._providers:
            raise NotFoundError(f"provider not registered: {name}")
        return self._providers[name]

    def get_instance(self, name: str) -> Provider:
        if name not in self._instances:
            raise NotFoundError(f"provider instance not registered: {name}")
        return self._instances[name]

    def instances(self) -> list[Provider]:
        return [self._instances[name] for name in sorted(self._instances)]

    def select(
        self,
        *,
        required_capability: str | None = None,
        latency_budget_ms: float | None = None,
        cost_budget: float | None = None,
        require_local: bool = False,
        require_privacy_approved: bool = True,
        prefer: tuple[str, ...] = (),
    ) -> ProviderProfile:
        """Deterministically select the best provider for a requirement set."""
        candidates = [
            p
            for p in self._providers.values()
            if p.supports(required_capability)
            and (latency_budget_ms is None or p.latency_ms <= latency_budget_ms)
            and (cost_budget is None or p.cost_per_call <= cost_budget)
            and (not require_local or p.local)
            and (not require_privacy_approved or p.privacy_approved)
        ]
        if not candidates:
            raise CapabilityError(
                f"no provider satisfies required_capability={required_capability!r}"
            )
        for name in prefer:
            for candidate in candidates:
                if candidate.name == name:
                    return candidate
        return min(
            candidates,
            key=lambda p: (-p.reliability, p.latency_ms, p.cost_per_call, len(p.capabilities)),
        )

    def names(self) -> list[str]:
        return sorted(self._providers)


__all__ = [
    "Provider",
    "ProviderPolicy",
    "ProviderProfile",
    "ProviderRegistry",
    "ProviderUsage",
]