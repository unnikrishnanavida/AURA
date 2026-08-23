"""AURA SDK Adapters types."""

from __future__ import annotations
from dataclasses import dataclass
from typing import Any


@dataclass
class TypeDefinition:
    """Structured metadata for aura_sdk.adapters."""

    name: str
    enabled: bool = True
    metadata: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-serializable representation of the type metadata."""
        return {
            "name": self.name,
            "enabled": self.enabled,
            "metadata": self.metadata or {},
        }


__all__ = ["TypeDefinition"]
