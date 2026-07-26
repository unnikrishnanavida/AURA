"""
AURA Contracts - Command
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
import uuid


@dataclass(slots=True)
class Command:
    """Base command."""

    name: str

    id: str = field(default_factory=lambda: str(uuid.uuid4()))

    timestamp: datetime = field(default_factory=datetime.utcnow)