"""Core domain models for registry entries."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class RegistryMetadata:
    """Describes metadata associated with a registry entry."""

    version: str = "1.0"
    description: str = ""
    tags: list[str] = field(default_factory=list)
    enabled: bool = True
    owner: str | None = None


@dataclass(slots=True)
class RegistryEntry:
    """Represents a registry entry used throughout the subsystem."""

    name: str
    kind: str
    data: dict[str, Any] = field(default_factory=dict)
    metadata: RegistryMetadata = field(default_factory=RegistryMetadata)

    def to_dict(self) -> dict[str, Any]:
        """Return a serializable representation."""
        return {
            "name": self.name,
            "kind": self.kind,
            "data": self.data,
            "metadata": {
                "version": self.metadata.version,
                "description": self.metadata.description,
                "tags": self.metadata.tags,
                "enabled": self.metadata.enabled,
                "owner": self.metadata.owner,
            },
        }

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "RegistryEntry":
        """Create an entry from a dictionary."""
        metadata_payload = payload.get("metadata", {})
        return cls(
            name=payload["name"],
            kind=payload["kind"],
            data=payload.get("data", {}),
            metadata=RegistryMetadata(
                version=metadata_payload.get("version", "1.0"),
                description=metadata_payload.get("description", ""),
                tags=list(metadata_payload.get("tags", [])),
                enabled=metadata_payload.get("enabled", True),
                owner=metadata_payload.get("owner"),
            ),
        )
