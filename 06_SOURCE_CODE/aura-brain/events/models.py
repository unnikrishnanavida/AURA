"""Data models for the events subsystem."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class EventsModel:
    """Represents a domain object in the events subsystem."""

    name: str
    data: dict[str, Any] = field(default_factory=dict)
