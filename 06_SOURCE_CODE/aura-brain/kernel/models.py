"""Data models for the kernel subsystem."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class KernelModel:
    """Represents a domain object in the kernel subsystem."""

    name: str
    data: dict[str, Any] = field(default_factory=dict)
