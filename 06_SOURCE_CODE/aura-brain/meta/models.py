"""Data models for the meta subsystem."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class MetaModel:
    """Represents a domain object in the meta subsystem."""

    name: str
    data: dict[str, Any] = field(default_factory=dict)
