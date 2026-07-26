"""
AURA Contracts - Message
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any
import uuid


@dataclass(slots=True)
class Message:
    """Base transport message."""

    sender: str

    receiver: str

    payload: Any

    id: str = field(default_factory=lambda: str(uuid.uuid4()))

    created_at: datetime = field(default_factory=datetime.utcnow)