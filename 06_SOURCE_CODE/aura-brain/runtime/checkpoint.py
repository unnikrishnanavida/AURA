"""
Runtime Checkpoint
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass(slots=True)
class Checkpoint:
    """Represents a runtime checkpoint."""

    task_id: str

    state: str

    data: dict[str, Any] = field(default_factory=dict)

    created_at: datetime = field(default_factory=datetime.utcnow)