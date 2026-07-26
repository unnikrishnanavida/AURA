"""Data models for the missions subsystem."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class MissionsModel:
    """Represents a domain object in the missions subsystem."""

    name: str
    data: dict[str, Any] = field(default_factory=dict)
