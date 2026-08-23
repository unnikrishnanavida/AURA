"""Capability registry: registration, lookup, and deterministic matching."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable

from aura_agent.capability_discovery.models import Capability, CapabilityMatch, MatchStatus

__all__ = ["CapabilityRegistry", "RegistryDiagnostics"]


@dataclass(frozen=True)
class RegistryDiagnostics:
    """Matching diagnostics: what was searched and why the outcome was reached."""

    total_candidates: int
    availability_blocked: list[str]
    scope_blocked: list[str]


class CapabilityRegistry:
    """Owns the set of registered capabilities.

    Matching is exact and deterministic:

    - ``filesystem.write`` required, registry contains ``filesystem.write``
      -> ``MATCH``
    - ``database.delete`` required, registry contains only ``database.read``
      -> ``DENY``
    - scopes on the registered capability constrain matches
    - an unavailable capability is reported as ``DENY`` with a reason, never
      silently matched
    """

    def __init__(self) -> None:
        self._capabilities: dict[str, Capability] = {}

    def register(self, capability: Capability) -> None:
        """Register a capability, replacing a same-named prior registration."""
        if capability.name in self._capabilities and not capability.available:
            # preserving availability is deliberate: re-registering the same
            # name as unavailable marks it out-of-service rather than removing it
            pass
        self._capabilities[capability.name] = capability

    def unregister(self, name: str) -> None:
        """Remove a capability from the registry."""
        self._capabilities.pop(name, None)

    def set_availability(self, name: str, available: bool) -> None:
        """Mark a capability available or unavailable without removing it."""
        cap = self._capabilities.get(name)
        if cap is not None:
            self._capabilities[name] = Capability(
                name=cap.name,
                description=cap.description,
                version=cap.version,
                owner_agent=cap.owner_agent,
                available=available,
                scopes=cap.scopes,
                metadata=cap.metadata,
            )

    def get(self, name: str) -> Capability | None:
        return self._capabilities.get(name)

    def has(self, name: str) -> bool:
        return name in self._capabilities

    def names(self) -> list[str]:
        return sorted(self._capabilities)

    def all(self) -> list[Capability]:
        return list(self._capabilities.values())

    def match(self, required: str, *, scopes: Iterable[str] | None = None) -> CapabilityMatch:
        """Match ``required`` against the registry.

        Raises ``ValueError`` for a malformed requirement (missing dot
        namespace) so typos surface loudly instead of silently denying.
        """
        if not isinstance(required, str) or not required or "." not in required:
            raise ValueError(f"malformed capability requirement: {required!r}")

        scope_set = frozenset(scopes or [])
        candidates = [
            cap for cap in self._capabilities.values() if cap.name == required or cap.satisfies(required)
        ]

        diagnostics = RegistryDiagnostics(
            total_candidates=len([c for c in self._capabilities.values()]),
            availability_blocked=[],
            scope_blocked=[],
        )

        for cap in sorted(candidates, key=lambda c: c.name):
            if not cap.available:
                diagnostics.availability_blocked.append(cap.name)
                continue
            if scope_set and cap.scopes and not (scope_set & frozenset(cap.scopes)):
                diagnostics.scope_blocked.append(cap.name)
                continue
            return CapabilityMatch(
                required=required,
                status=MatchStatus.MATCH,
                matched=cap,
                reason=f"matched registered capability {cap.name!r}",
            )

        if candidates:
            return CapabilityMatch(
                required=required,
                status=MatchStatus.DENY,
                reason=(
                    "candidate capabilities exist but are unavailable or "
                    f"out of scope: {sorted(diagnostics.availability_blocked + diagnostics.scope_blocked)!r}"
                ),
            )
        return CapabilityMatch(
            required=required,
            status=MatchStatus.DENY,
            reason=f"no registered capability matches {required!r}",
        )

    def __len__(self) -> int:
        return len(self._capabilities)