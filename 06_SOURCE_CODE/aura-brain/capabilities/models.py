"""Data models for the capabilities subsystem."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class CapabilitiesModel:
    """Represents a domain object in the capabilities subsystem."""

    name: str
    data: dict[str, Any] = field(default_factory=dict)
