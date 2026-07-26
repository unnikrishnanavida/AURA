"""Data models for the security subsystem."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class SecurityModel:
    """Represents a domain object in the security subsystem."""

    name: str
    data: dict[str, Any] = field(default_factory=dict)
