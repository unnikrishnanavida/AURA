"""Data models for the research subsystem."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class ResearchModel:
    """Represents a domain object in the research subsystem."""

    name: str
    data: dict[str, Any] = field(default_factory=dict)
