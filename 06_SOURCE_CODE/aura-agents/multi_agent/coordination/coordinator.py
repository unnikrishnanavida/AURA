"""Multi-agent coordination models and coordinator."""

from __future__ import annotations

import enum
from dataclasses import dataclass, field

from aura_agent.contracts.ids import AgentId, GoalId
from aura_agent.multi_agent.communication.message_bus import MessageBus
from aura_agent.multi_agent.communication.models import AgentMessage

__all__ = [
    "CoordinationRole",
    "CoordinationState",
    "SharedGoal",
    "Coordinator",
]


class CoordinationRole(enum.Enum):
    """Roles in a multi-agent effort."""

    ORCHESTRATOR = "orchestrator"
    WORKER = "worker"
    OBSERVER = "observer"


class CoordinationState(enum.Enum):
    """Lifecycle of a shared coordination."""

    ADVERTISED = "advertised"
    ACTIVE = "active"
    COMPLETED = "completed"
    ABORTED = "aborted"


@dataclass
class SharedGoal:
    """The shared coordination record."""

    coordination_id: str
    goal: GoalId
    participants: list[AgentId]
    state: dict = field(default_factory=dict)
    status: CoordinationState = CoordinationState.ADVERTISED


class Coordinator:
    """Drives a shared goal across agents through the message bus."""

    def __init__(self, bus: MessageBus, *, coordinator: AgentId) -> None:
        self._bus = bus
        self._coordinator = coordinator
        self._shared: dict[str, SharedGoal] = {}

    def advertise(
        self,
        *,
        coordination_id: str,
        goal: GoalId,
        participants: list[AgentId],
    ) -> SharedGoal:
        """Broadcast a shared goal to participants and record it."""
        shared = SharedGoal(
            coordination_id=coordination_id,
            goal=goal,
            participants=list(participants),
        )
        self._shared[coordination_id] = shared
        for participant in participants:
            self._bus.send(
                AgentMessage(
                    kind="broadcast",
                    sender=self._coordinator,
                    recipient=participant,
                    payload={
                        "coordination_id": coordination_id,
                        "goal": str(goal),
                    },
                )
            )
        return shared

    def activation(self, coordination_id: str) -> SharedGoal:
        shared = self.state_of(coordination_id)
        shared.status = CoordinationState.ACTIVE
        return shared

    def state_of(self, coordination_id: str) -> SharedGoal:
        if coordination_id not in self._shared:
            raise KeyError(f"unknown coordination {coordination_id}")
        return self._shared[coordination_id]

    def complete(self, coordination_id: str) -> None:
        self.state_of(coordination_id).status = CoordinationState.COMPLETED

    def abort(self, coordination_id: str) -> None:
        self.state_of(coordination_id).status = CoordinationState.ABORTED

    def all_coordinations(self) -> list[SharedGoal]:
        return list(self._shared.values())
