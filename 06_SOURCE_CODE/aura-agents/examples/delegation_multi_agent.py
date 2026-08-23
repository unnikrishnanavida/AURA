"""Delegation + multi-agent example: an orchestrator delegates work to a
capable worker selected by reputation.

Run with:  python examples/delegation_multi_agent.py
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from aura_agent import dsl
from aura_agent.capability_discovery.registry.agent_registry import (
    AgentCapabilityRegistry,
)
from aura_agent.contracts.ids import AgentId, GoalId
from aura_agent.delegation import DelegationEngine, TaskRequirements
from aura_agent.multi_agent import Coordinator, MessageBus
from aura_agent.reputation import AgentOutcome, ReputationLedger, ReputationScorer
from aura_agent.tools import Tool


def main() -> None:
    # reputation evidence: worker-a is reliable
    ledger = ReputationLedger()
    a = AgentId("ag-worker-a")
    b = AgentId("ag-worker-b")
    for _ in range(5):
        ledger.record(AgentOutcome(agent_id=a, action="t", success=True))
    for _ in range(5):
        ledger.record(AgentOutcome(agent_id=b, action="t", success=False))

    # capability index: only A can do `worker.a`
    caps = AgentCapabilityRegistry()
    caps.register(a, {"worker.a"}, available=True)
    caps.register(b, {"worker.b"}, available=True)

    orchestrator = dsl.AgentBuilder(name="orchestrator").build()
    delegation = DelegationEngine(capabilities=caps, reputation=ReputationScorer(ledger))

    task = delegation.create_task(
        task_id="task-1",
        delegator=orchestrator.agent_id,
        requirements=TaskRequirements(required_capabilities=("worker.a",)),
    )
    chosen = delegation.select_worker(
        task_id=task.task_id, requirements=task.requirements
    )
    proposal = delegation.propose(task_id=task.task_id, worker=chosen)
    delegation.agree(task_id=task.task_id, worker=chosen)
    print(f"delegated to {chosen} (proposal {proposal.proposal_id if proposal else 'none'})")

    # multi-agent coordination via the message bus
    bus = MessageBus()
    coordinator = Coordinator(bus, coordinator=orchestrator.agent_id)
    shared = coordinator.advertise(
        coordination_id="coord-1", goal=GoalId.new(), participants=[a]
    )
    print(f"coordination advertised to {len(shared.participants)} agent(s)")


if __name__ == "__main__":
    main()