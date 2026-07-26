"""Data models for the plugins subsystem."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class PluginsModel:
    """Represents a domain object in the plugins subsystem."""

    name: str
    data: dict[str, Any] = field(default_factory=dict)
