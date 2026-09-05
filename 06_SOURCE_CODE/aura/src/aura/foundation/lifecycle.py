"""Lifecycle primitives.

AURA components follow one lifecycle contract: CREATED -> STARTING -> RUNNING
-> STOPPING -> STOPPED, with FAILED as a terminal error state. The
:class:`LifecycleGuard` enforces legal transitions and records history.
"""

from __future__ import annotations

from enum import StrEnum
from typing import Any, Protocol, runtime_checkable

from aura.foundation.errors import InvalidStateTransitionError


class LifecycleState(StrEnum):
    CREATED = "created"
    STARTING = "starting"
    RUNNING = "running"
    STOPPING = "stopping"
    STOPPED = "stopped"
    FAILED = "failed"


_TRANSITIONS: dict[LifecycleState, frozenset[LifecycleState]] = {
    LifecycleState.CREATED: frozenset({LifecycleState.STARTING}),
    LifecycleState.STARTING: frozenset({LifecycleState.RUNNING, LifecycleState.FAILED, LifecycleState.STOPPING}),
    LifecycleState.RUNNING: frozenset({LifecycleState.STOPPING, LifecycleState.FAILED}),
    LifecycleState.STOPPING: frozenset({LifecycleState.STOPPED, LifecycleState.FAILED}),
    LifecycleState.STOPPED: frozenset({LifecycleState.STARTING, LifecycleState.FAILED}),
    LifecycleState.FAILED: frozenset(),
}


class LifecycleGuard:
    """Enforces lifecycle state transitions with full history."""

    def __init__(self) -> None:
        self.state = LifecycleState.CREATED
        self.history: list[LifecycleState] = [LifecycleState.CREATED]

    def transition(self, target: LifecycleState) -> None:
        if target not in _TRANSITIONS[self.state]:
            raise InvalidStateTransitionError(
                f"invalid lifecycle transition {self.state.value} -> {target.value}"
            )
        self.state = target
        self.history.append(target)

    def assert_running(self, component: str = "component") -> None:
        if self.state is not LifecycleState.RUNNING:
            raise InvalidStateTransitionError(
                f"{component} must be RUNNING to perform this operation (state={self.state.value})"
            )


@runtime_checkable
class Component(Protocol):
    """The contract every managed AURA service implements."""

    name: str

    def start(self) -> None: ...

    def stop(self) -> None: ...

    def health(self) -> dict[str, Any]: ...


__all__ = ["Component", "LifecycleGuard", "LifecycleState"]