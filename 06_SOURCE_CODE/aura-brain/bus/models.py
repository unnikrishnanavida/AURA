"""Data models for the bus subsystem."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class BusModel:
    """Represents a domain object in the bus subsystem."""

    name: str
    data: dict[str, Any] = field(default_factory=dict)
