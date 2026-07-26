"""Data models for the shared subsystem."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class SharedModel:
    """Represents a domain object in the shared subsystem."""

    name: str
    data: dict[str, Any] = field(default_factory=dict)
