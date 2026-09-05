"""Capability gate (default-deny) for aura-desktop.

The gate grants nothing by default: only explicitly allowed capabilities pass.
This is the same fail-closed posture as the rest of the ecosystem.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class CapabilityGate:
    """Default-deny capability gate."""

    allowed: set[str] = field(default_factory=set)

    def grant(self, capability: str) -> None:
        self.allowed.add(capability)

    def revoke(self, capability: str) -> None:
        self.allowed.discard(capability)

    def check(self, capability: str) -> bool:
        return capability in self.allowed

    def require(self, capability: str) -> None:
        if not self.check(capability):
            raise PermissionError(f"capability not granted: {capability}")


__all__ = ["CapabilityGate"]