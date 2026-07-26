"""Data models for the storage subsystem."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class StorageModel:
    """Represents a domain object in the storage subsystem."""

    name: str
    data: dict[str, Any] = field(default_factory=dict)
