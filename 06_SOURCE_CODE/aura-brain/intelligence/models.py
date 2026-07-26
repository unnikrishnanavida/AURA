"""Data models for the intelligence subsystem."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class IntelligenceModel:
    """Represents a domain object in the intelligence subsystem."""

    name: str
    data: dict[str, Any] = field(default_factory=dict)
