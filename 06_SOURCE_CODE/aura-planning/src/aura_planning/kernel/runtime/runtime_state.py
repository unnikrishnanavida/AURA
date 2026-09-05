from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
from time import monotonic
from typing import Any

class RuntimePhase(str, Enum):
    CREATED="created"; INITIALIZING="initializing"; READY="ready"
    RUNNING="running"; STOPPING="stopping"; STOPPED="stopped"; FAILED="failed"

@dataclass(slots=True)
class RuntimeState:
    phase: RuntimePhase = RuntimePhase.CREATED
    started_at: float | None = None
    stopped_at: float | None = None
    error: str | None = None
    counters: dict[str,int] = field(default_factory=dict)
    metadata: dict[str,Any] = field(default_factory=dict)

    def transition(self, phase: RuntimePhase, error: str|None=None) -> None:
        allowed = {
            RuntimePhase.CREATED:{RuntimePhase.INITIALIZING,RuntimePhase.FAILED},
            RuntimePhase.INITIALIZING:{RuntimePhase.READY,RuntimePhase.FAILED},
            RuntimePhase.READY:{RuntimePhase.RUNNING,RuntimePhase.STOPPING,RuntimePhase.FAILED},
            RuntimePhase.RUNNING:{RuntimePhase.READY,RuntimePhase.STOPPING,RuntimePhase.FAILED},
            RuntimePhase.STOPPING:{RuntimePhase.STOPPED,RuntimePhase.FAILED},
            RuntimePhase.STOPPED:set(),
            RuntimePhase.FAILED:{RuntimePhase.STOPPING,RuntimePhase.STOPPED},
        }
        if phase != self.phase and phase not in allowed[self.phase]:
            raise RuntimeError(f"invalid runtime transition {self.phase.value}->{phase.value}")
        self.phase=phase; self.error=error
        if phase == RuntimePhase.RUNNING and self.started_at is None: self.started_at=monotonic()
        if phase == RuntimePhase.STOPPED: self.stopped_at=monotonic()

    def increment(self, name:str, amount:int=1)->int:
        if amount < 0: raise ValueError("amount must be non-negative")
        self.counters[name]=self.counters.get(name,0)+amount
        return self.counters[name]
