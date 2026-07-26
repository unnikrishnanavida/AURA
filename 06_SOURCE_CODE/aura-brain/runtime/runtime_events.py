"""
Runtime Events
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum


class RuntimeEventType(Enum):
    STARTED = "started"
    STOPPED = "stopped"
    TASK_SUBMITTED = "task_submitted"
    TASK_STARTED = "task_started"
    TASK_COMPLETED = "task_completed"
    TASK_FAILED = "task_failed"


@dataclass(slots=True)
class RuntimeEvent:
    """Represents a runtime event."""

    event_type: RuntimeEventType
    timestamp: datetime
    source: str
    payload: dict | None = None