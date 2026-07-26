"""Data models for the evolution subsystem."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class EvolutionModel:
    """Represents a domain object in the evolution subsystem."""

    name: str
    data: dict[str, Any] = field(default_factory=dict)
