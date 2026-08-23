"""Execution state machine.

Explicit states and valid transitions. Invalid transitions raise
:class:`~aura_agent.contracts.errors.InvalidStateTransition`; every accepted
transition is appended to a recorded history so trajectory analysis can use it.
"""

from __future__ import annotations

import enum
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import ClassVar

from aura_agent.contracts.errors import InvalidStateTransition

__all__ = ["ExecutionState", "StateMachine", "transition_table"]


class ExecutionState(enum.Enum):
    """The lifecycle of a single execution.

    The enum intentionally mirrors the lifecycle mandated by the AURA Agent
    architecture: an execution is created ``PENDING``, is validated to
    ``READY``, runs, and terminates in one of the terminal states. Invalid
    transitions are rejected by :class:`StateMachine`.
    """

    PENDING = "pending"
    READY = "ready"
    RUNNING = "running"
    WAITING = "waiting"
    BLOCKED = "blocked"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    CANCELLED = "cancelled"
    RECOVERING = "recovering"
    ROLLED_BACK = "rolled_back"

    def __str__(self) -> str:  # pragma: no cover - trivial
        return self.value


#: Allowed transitions. Maps source state -> set of target states.
transition_table: ClassVar[dict[ExecutionState, frozenset[ExecutionState]]] = {
    ExecutionState.PENDING: frozenset({ExecutionState.READY, ExecutionState.CANCELLED}),
    ExecutionState.READY: frozenset(
        {ExecutionState.RUNNING, ExecutionState.CANCELLED, ExecutionState.BLOCKED}
    ),
    ExecutionState.RUNNING: frozenset(
        {
            ExecutionState.SUCCEEDED,
            ExecutionState.FAILED,
            ExecutionState.WAITING,
            ExecutionState.BLOCKED,
            ExecutionState.CANCELLED,
            ExecutionState.RECOVERING,
            ExecutionState.ROLLED_BACK,
        }
    ),
    ExecutionState.WAITING: frozenset({ExecutionState.RUNNING, ExecutionState.CANCELLED}),
    ExecutionState.BLOCKED: frozenset(
        {ExecutionState.READY, ExecutionState.CANCELLED, ExecutionState.FAILED}
    ),
    ExecutionState.RECOVERING: frozenset(
        {
            ExecutionState.RUNNING,
            ExecutionState.READY,
            ExecutionState.FAILED,
            ExecutionState.ROLLED_BACK,
            ExecutionState.CANCELLED,
        }
    ),
    # terminal states: no outgoing transitions
    ExecutionState.SUCCEEDED: frozenset(),
    ExecutionState.FAILED: frozenset(),
    ExecutionState.CANCELLED: frozenset(),
    ExecutionState.ROLLED_BACK: frozenset(),
}


@dataclass
class TransitionRecord:
    """A single recorded state transition."""

    from_state: ExecutionState
    to_state: ExecutionState
    timestamp: datetime
    reason: str = ""


@dataclass
class StateMachine:
    """Owns the current state of one execution and validates transitions."""

    state: ExecutionState = ExecutionState.PENDING
    history: list[TransitionRecord] = field(default_factory=list)

    def transition(
        self, target: ExecutionState, *, reason: str = ""
    ) -> ExecutionState:
        """Move to ``target`` if the transition is valid.

        Raises :class:`InvalidStateTransition` otherwise. Every successful
        transition is recorded in :attr:`history`.
        """
        if target is self.state:
            return self.state
        allowed = transition_table.get(self.state, frozenset())
        if target not in allowed:
            raise InvalidStateTransition(self.state.value, target.value)
        self.history.append(
            TransitionRecord(
                from_state=self.state,
                to_state=target,
                timestamp=datetime.now(UTC),
                reason=reason,
            )
        )
        self.state = target
        return target

    def can_transition(self, target: ExecutionState) -> bool:
        """Return whether the transition is currently allowed."""
        return target in transition_table.get(self.state, frozenset())

    @property
    def is_terminal(self) -> bool:
        """True when the execution reached a terminal state."""
        return self.state in {
            ExecutionState.SUCCEEDED,
            ExecutionState.FAILED,
            ExecutionState.CANCELLED,
            ExecutionState.ROLLED_BACK,
        }