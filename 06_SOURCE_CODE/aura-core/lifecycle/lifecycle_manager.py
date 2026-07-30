from __future__ import annotations

from typing import List
from .lifecycle_hooks import LifecycleHooks
from .lifecycle_state import LifecycleState


class LifecycleManager:
    def __init__(self) -> None:
        self._state = LifecycleState.INITIAL
        self._hooks = LifecycleHooks()

    def add_start_hook(self, fn) -> None:
        self._hooks.on_start(fn)

    def add_stop_hook(self, fn) -> None:
        self._hooks.on_stop(fn)

    def start(self) -> None:
        self._state = LifecycleState.STARTING
        self._hooks.run_start()
        self._state = LifecycleState.RUNNING

    def stop(self) -> None:
        self._state = LifecycleState.STOPPING
        self._hooks.run_stop()
        self._state = LifecycleState.STOPPED

    @property
    def state(self) -> LifecycleState:
        return self._state
