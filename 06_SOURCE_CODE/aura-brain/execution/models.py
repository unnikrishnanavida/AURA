"""Data models for the execution subsystem."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class ExecutionModel:
    """Represents a domain object in the execution subsystem."""

    name: str
    data: dict[str, Any] = field(default_factory=dict)
