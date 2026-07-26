"""Data models for the prediction subsystem."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class PredictionModel:
    """Represents a domain object in the prediction subsystem."""

    name: str
    data: dict[str, Any] = field(default_factory=dict)
