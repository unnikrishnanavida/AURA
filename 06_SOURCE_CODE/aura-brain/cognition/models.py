"""Data models for the cognition subsystem."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class CognitionModel:
    """Represents a domain object in the cognition subsystem."""

    name: str
    data: dict[str, Any] = field(default_factory=dict)
