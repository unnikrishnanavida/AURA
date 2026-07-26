"""
AURA Contracts - Metadata
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime


@dataclass(slots=True)
class Metadata:
    """Common metadata attached to contracts."""

    correlation_id: str = ""

    trace_id: str = ""

    source: str = ""

    destination: str = ""

    user_id: str = ""

    session_id: str = ""

    created_at: datetime = field(default_factory=datetime.utcnow)

    tags: dict[str, str] = field(default_factory=dict)