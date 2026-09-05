"""Capability requirement and matching."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class CapabilityRequirement:
    """What an action needs: a named capability with an operation."""

    name: str
    operation: str = "*"


__all__ = ["CapabilityRequirement"]