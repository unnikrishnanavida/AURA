"""Capability matching: does a registered capability satisfy a requirement?"""

from __future__ import annotations

from typing import Any


def matches(requirement: Any, capability: Any) -> bool:
    """Return whether ``capability`` satisfies ``requirement``.

    A capability satisfies a requirement when the names match and the
    capability lists the required operation (or ``*``).
    """
    if capability is None:
        return False
    if capability.name != requirement.name:
        return False
    operations: frozenset[str] = getattr(capability, "operations", None) or frozenset()
    return requirement.operation in operations or "*" in operations


__all__ = ["matches"]