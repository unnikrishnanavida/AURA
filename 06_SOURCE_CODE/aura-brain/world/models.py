"""Data models for the world subsystem."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class WorldModel:
    """Represents a domain object in the world subsystem."""

    name: str
    data: dict[str, Any] = field(default_factory=dict)
