"""Data models for the monitoring subsystem."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class MonitoringModel:
    """Represents a domain object in the monitoring subsystem."""

    name: str
    data: dict[str, Any] = field(default_factory=dict)
