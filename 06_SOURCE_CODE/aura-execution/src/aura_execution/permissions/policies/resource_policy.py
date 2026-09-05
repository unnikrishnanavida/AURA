"""Resource policy: scoped access to capabilities."""

from __future__ import annotations

from typing import Any


class ResourcePolicy:
    """Decides whether a capability is usable within a set of scopes."""

    def __init__(self, allowed: dict[str, frozenset[str]] | None = None) -> None:
        self.allowed = allowed or {}

    def grant(self, capability: str, scopes: frozenset[str]) -> None:
        self.allowed[capability] = scopes

    def allows(self, capability: str, scopes: Any) -> bool:
        permitted = self.allowed.get(capability)
        if permitted is None:
            # No explicit restriction -> everything is allowed in the default
            # resource policy; restrictiveness is configured declaratively.
            return True
        request_scopes = set(scopes or set())
        return bool(permitted & request_scopes) or "*" in permitted


__all__ = ["ResourcePolicy"]