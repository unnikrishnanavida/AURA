from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any
import uuid


@dataclass(slots=True)
class Task:
    """Represents a runtime task."""

    name: str
    payload: Any = None

    id: str = field(default_factory=lambda: str(uuid.uuid4()))

    created_at: datetime = field(default_factory=datetime.utcnow)

    priority: int = 5