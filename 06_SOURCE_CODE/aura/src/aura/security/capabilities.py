"""Deterministic capability matching.

A capability is an explicit, versioned permission-to-do one thing (e.g.
``filesystem.read``). Execution requires an explicit capability grant;
this layer is the single authority for capability resolution.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from aura.foundation.errors import CapabilityError, NotFoundError


@dataclass(frozen=True, slots=True)
class Capability:
    name: str
    metadata: dict[str, Any] = field(default_factory=dict)
    scope: str = "*"
    available: bool = True

    def __post_init__(self) -> None:
        if not self.name:
            raise ValueError(f"invalid capability name: {self.name!r}")


def _segments(name: str) -> list[str]:
    return name.split(".")


def name_matches(pattern: str, name: str) -> bool:
    """Match a capability pattern supporting ``*`` wildcards, e.g. ``filesystem.*``."""
    p, n = _segments(pattern), _segments(name)
    if len(n) < len(p):
        return False
    for i, seg in enumerate(p):
        if seg == "*":
            return True
        if i >= len(n) or n[i] != seg:
            return False
    return True


class CapabilityRegistry:
    def __init__(self) -> None:
        self._caps: dict[str, Capability] = {}

    def register(self, capability: Capability) -> None:
        self._caps[capability.name] = capability

    def get(self, name: str) -> Capability:
        if name not in self._caps:
            raise NotFoundError(f"capability not registered: {name}")
        return self._caps[name]

    def has(self, name: str) -> bool:
        return name in self._caps

    def require(self, name: str) -> Capability:
        if name not in self._caps:
            raise CapabilityError(f"capability not granted: {name}")
        if not self._caps[name].available:
            raise CapabilityError(f"capability unavailable: {name}")
        return self._caps[name]

    def names(self) -> list[str]:
        return sorted(self._caps)

    def diagnostics(self) -> dict[str, Any]:
        return {
            name: {"available": cap.available, "scope": cap.scope}
            for name, cap in sorted(self._caps.items())
        }


__all__ = ["Capability", "CapabilityRegistry", "name_matches"]