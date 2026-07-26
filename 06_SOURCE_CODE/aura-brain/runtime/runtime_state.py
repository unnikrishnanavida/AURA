from __future__ import annotations

from enum import Enum, auto


class RuntimeState(Enum):
    """Represents the runtime lifecycle."""

    CREATED = auto()
    STARTING = auto()
    RUNNING = auto()
    PAUSED = auto()
    STOPPING = auto()
    STOPPED = auto()
    FAILED = auto()