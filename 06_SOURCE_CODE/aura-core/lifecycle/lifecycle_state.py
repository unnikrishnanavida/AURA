from __future__ import annotations

from enum import Enum


class LifecycleState(Enum):
    INITIAL = "initial"
    STARTING = "starting"
    RUNNING = "running"
    STOPPING = "stopping"
    STOPPED = "stopped"
