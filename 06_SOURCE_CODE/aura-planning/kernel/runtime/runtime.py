from __future__ import annotations
from contextlib import contextmanager
from typing import Iterator
from .planning_context import PlanningContext
from .resource_manager import ResourceManager
from .runtime_state import RuntimePhase,RuntimeState

class PlanningRuntime:
    def __init__(self)->None:
        self.state=RuntimeState(); self.resources=ResourceManager(); self.context:PlanningContext|None=None
    def initialize(self,context:PlanningContext)->None:
        self.state.transition(RuntimePhase.INITIALIZING); self.context=context; self.state.transition(RuntimePhase.READY)
    @contextmanager
    def execution(self)->Iterator[PlanningContext]:
        if self.context is None: raise RuntimeError("runtime not initialized")
        self.state.transition(RuntimePhase.RUNNING); self.state.increment("executions")
        try: yield self.context
        except Exception as exc:
            self.state.transition(RuntimePhase.FAILED,str(exc)); raise
        else: self.state.transition(RuntimePhase.READY)
    def shutdown(self)->None:
        if self.state.phase in {RuntimePhase.CREATED,RuntimePhase.STOPPED}: return
        self.state.transition(RuntimePhase.STOPPING); self.context=None; self.state.transition(RuntimePhase.STOPPED)
