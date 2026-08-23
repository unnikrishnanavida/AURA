"""Delegation engine: controlled task hand-off to capable, trusted workers.

Delegation never assumes another agent is trustworthy. An agent is only
eligible to be delegated a task when:

1. it is registered as available and capable of every required capability, and
2. it is chosen deterministically among eligible agents by reputation
   (reliability first, then confidence, then lowest cost).

Delegated work remains subject to the parent agent's capability, permission,
safety, and budget rules during execution (enforced by the execution engine).
"""

from __future__ import annotations

from typing import Any

from aura_agent.capability_discovery.registry.agent_registry import (
    AgentCapabilityRegistry,
)
from aura_agent.contracts.ids import AgentId
from aura_agent.delegation.models import (
    DelegatedTask,
    Proposal,
    TaskRequirements,
    TaskStatus,
)
from aura_agent.reputation.reputation_engine import ReputationScorer

__all__ = ["DelegationEngine"]


class DelegationEngine:
    """Selects workers, tracks proposals, and manages task lifecycle."""

    def __init__(
        self,
        capabilities: AgentCapabilityRegistry,
        reputation: ReputationScorer,
    ) -> None:
        self._caps = capabilities
        self._reputation = reputation
        self._tasks: dict[str, DelegatedTask] = {}
        self._proposals: dict[str, list[Proposal]] = {}

    # -- task lifecycle -----------------------------------------------------------
    def create_task(
        self,
        *,
        task_id: str,
        delegator: AgentId,
        requirements: TaskRequirements,
    ) -> DelegatedTask:
        task = DelegatedTask(
            task_id=task_id,
            delegator=delegator,
            requirements=requirements,
            status=TaskStatus.PENDING,
        )
        self._tasks[task_id] = task
        return task

    def eligible_workers(self, requirements: TaskRequirements) -> list[AgentId]:
        """Available agents capable of every required capability."""
        if not requirements.required_capabilities:
            return []
        eligible: set[AgentId] = set()
        first = True
        for req in requirements.required_capabilities:
            agents = {
                entry.agent_id
                for entry in self._caps.matching_agents(req)
            }
            eligible = agents if first else (eligible & agents)
            first = False
        return sorted(eligible)

    def select_worker(
        self,
        *,
        task_id: str,
        requirements: TaskRequirements,
        min_reliability: float = 0.0,
    ) -> AgentId | None:
        """Choose the best worker by reputation among eligible agents."""
        eligible = self.eligible_workers(requirements)
        best: AgentId | None = None
        best_score: tuple[float, float, float] | None = None
        for agent_id in eligible:
            score = self._reputation.score(agent_id)
            if score.reliability < min_reliability:
                continue
            ranking = (score.reliability, score.confidence, -score.avg_cost)
            if best_score is None or ranking > best_score:
                best_score = ranking
                best = agent_id
        return best

    def propose(
        self, *, task_id: str, worker: AgentId, terms: dict[str, Any] | None = None
    ) -> Proposal | None:
        """A worker proposes to take on a task (must be eligible)."""
        task = self._tasks.get(task_id)
        if task is None:
            return None
        if worker not in self.eligible_workers(task.requirements):
            return None
        reliability = self._reputation.score(worker).reliability
        proposal = Proposal(
            task_id=task_id,
            worker=worker,
            terms=terms or {},
            reliability=reliability,
        )
        self._proposals.setdefault(task_id, []).append(proposal)
        task.status = TaskStatus.PROPOSED
        return proposal

    def agree(self, *, task_id: str, worker: AgentId) -> DelegatedTask | None:
        """Accept a worker for a task after proposal."""
        task = self._tasks.get(task_id)
        if task is None:
            return None
        task.worker = worker
        task.status = TaskStatus.AGREED
        return task

    def start(self, *, task_id: str) -> DelegatedTask | None:
        task = self._tasks.get(task_id)
        if task is not None:
            task.status = TaskStatus.IN_PROGRESS
        return task

    def complete(self, *, task_id: str, success: bool) -> DelegatedTask | None:
        task = self._tasks.get(task_id)
        if task is None:
            return None
        task.status = TaskStatus.COMPLETED if success else TaskStatus.FAILED
        return task

    def get(self, task_id: str) -> DelegatedTask | None:
        return self._tasks.get(task_id)

    def all_tasks(self) -> list[DelegatedTask]:
        return list(self._tasks.values())

    @property
    def proposals(self) -> dict[str, list[Proposal]]:
        return self._proposals
