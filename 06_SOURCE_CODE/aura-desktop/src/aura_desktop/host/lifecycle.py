"""Application lifecycle for aura-desktop with an explicit state machine.

The lifecycle transitions deterministically: stopped -> starting -> running
-> stopping -> stopped. Invalid transitions are rejected rather than silently
ignored.
"""

from __future__ import annotations

from collections.abc import Callable
from enum import StrEnum


class LifecycleState(StrEnum):
    STOPPED = "stopped"
    STARTING = "starting"
    RUNNING = "running"
    STOPPING = "stopping"
    FAILED = "failed"


_ALLOWED_TRANSITIONS: dict[LifecycleState, set[LifecycleState]] = {
    LifecycleState.STOPPED: {LifecycleState.STARTING},
    LifecycleState.STARTING: {LifecycleState.RUNNING, LifecycleState.FAILED, LifecycleState.STOPPED},
    LifecycleState.RUNNING: {LifecycleState.STOPPING, LifecycleState.FAILED},
    LifecycleState.STOPPING: {LifecycleState.STOPPED, LifecycleState.FAILED},
    LifecycleState.FAILED: {LifecycleState.STOPPED},
}

Hook = Callable[[], None]


class InvalidLifecycleTransition(RuntimeError):
    """Raised when a state machine transition is not allowed."""


class ApplicationLifecycle:
    """An explicit, deterministic application lifecycle."""

    def __init__(self) -> None:
        self._state = LifecycleState.STOPPED
        self._hooks: dict[str, Hook] = {}

    @property
    def state(self) -> LifecycleState:
        return self._state

    def on(self, phase: str, hook: Hook) -> None:
        self._hooks[phase] = hook

    def _transition(self, target: LifecycleState) -> None:
        if target not in _ALLOWED_TRANSITIONS[self._state]:
            raise InvalidLifecycleTransition(f"cannot move from {self._state.value} to {target.value}")
        self._state = target
        hook = self._hooks.get(target.value)
        if hook is not None:
            hook()

    def start(self) -> LifecycleState:
        if self._state is LifecycleState.RUNNING:
            return self._state  # idempotent
        self._transition(LifecycleState.STARTING)
        self._transition(LifecycleState.RUNNING)
        return self._state

    def stop(self) -> LifecycleState:
        if self._state is LifecycleState.STOPPED:
            return self._state  # idempotent
        self._transition(LifecycleState.STOPPING)
        self._transition(LifecycleState.STOPPED)
        return self._state

    def fail(self) -> None:
        self._transition(LifecycleState.FAILED)

    def restart(self) -> LifecycleState:
        self.stop()
        return self.start()


__all__ = ["ApplicationLifecycle", "InvalidLifecycleTransition", "LifecycleState"]