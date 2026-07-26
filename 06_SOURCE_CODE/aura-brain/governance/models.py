"""Data models for the governance subsystem."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class GovernanceModel:
    """Represents a domain object in the governance subsystem."""

    name: str
    data: dict[str, Any] = field(default_factory=dict)
