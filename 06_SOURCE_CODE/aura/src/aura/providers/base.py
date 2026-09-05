"""Provider contracts and profiles."""

from __future__ import annotations

from dataclasses import dataclass

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


class ProviderRegistry:
    """Registry of known providers with deterministic selection."""

    def __init__(self) -> None:
        self._providers: dict[str, ProviderProfile] = {}

    def register(self, profile: ProviderProfile) -> None:
        self._providers[profile.name] = profile

    def get(self, name: str) -> ProviderProfile:
        if name not in self._providers:
            raise NotFoundError(f"provider not registered: {name}")
        return self._providers[name]

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


__all__ = ["ProviderProfile", "ProviderRegistry"]