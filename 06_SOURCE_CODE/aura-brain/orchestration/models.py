"""Data models for the orchestration subsystem."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class OrchestrationModel:
    """Represents a domain object in the orchestration subsystem."""

    name: str
    data: dict[str, Any] = field(default_factory=dict)
