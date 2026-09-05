"""AURA agents bridge.

Integrates the optional guarded agent runtime (``aura-agents``) behind the
platform. The bridge is intentionally the only entry point: delegated agents
inherit the platform's security boundaries (capabilities, permissions,
safety, budgets) and never bypass them.
"""

from __future__ import annotations

from typing import Any

_AGENTS_INSTALLED = False
try:
    import aura_agent  # type: ignore[import-not-found]  # noqa: F401

    _AGENTS_INSTALLED = True
except ImportError:  # pragma: no cover - optional dependency
    _AGENTS_INSTALLED = False


def agents_available() -> bool:
    """Return True when the optional AURA agents runtime is installed."""
    return _AGENTS_INSTALLED


class AgentsBridgeError(RuntimeError):
    """Raised when the agents runtime is required but not installed."""


def require_agents() -> Any:
    """Import the agents runtime or raise a helpful error."""
    if not _AGENTS_INSTALLED:
        raise AgentsBridgeError(
            "the AURA agents runtime is not installed; install with 'pip install aura[agents]'"
        )
    import aura_agent

    return aura_agent


__all__ = ["AgentsBridgeError", "agents_available", "require_agents"]