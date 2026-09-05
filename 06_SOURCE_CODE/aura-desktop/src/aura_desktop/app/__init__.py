"""AURA Desktop application entry point.

Provides :class:`AuraDesktop` — the desktop application facade over the
explicit lifecycle and a default-deny capability gate. This is a coherent
architecture, NOT a claim of a packaged, buildable native desktop app.
"""

from __future__ import annotations

from typing import Any

from aura_desktop.host.lifecycle import ApplicationLifecycle, LifecycleState
from aura_desktop.security.capabilities import CapabilityGate


class AuraDesktop:
    """Desktop application entry point with default-deny capability gate."""

    def __init__(self, capabilities: tuple[str, ...] = ()):
        self.lifecycle = ApplicationLifecycle()
        self.gate = CapabilityGate()
        for capability in capabilities:
            self.gate.grant(capability)

    @property
    def state(self) -> LifecycleState:
        return self.lifecycle.state

    def start(self) -> LifecycleState:
        return self.lifecycle.start()

    def stop(self) -> LifecycleState:
        return self.lifecycle.stop()

    def request(self, capability: str) -> dict[str, Any]:
        self.gate.require(capability)
        return {"allowed": True, "capability": capability}


__all__ = ["AuraDesktop"]