"""Reputation scoring from actual execution evidence.

Reputation is computed exclusively from recorded execution outcomes -- never
from arbitrary injected values. The runtime keeps a per-agent outcome ledger;
the scorer derives reliability, success rate, performance (cost), and
confidence from that evidence.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime

from aura_agent.contracts.ids import AgentId

__all__ = ["ReputationLedger", "ReputationScorer", "ReputationScore", "AgentOutcome"]


@dataclass(frozen=True)
class AgentOutcome:
    """A single recorded outcome for an agent."""

    agent_id: AgentId
    action: str
    success: bool
    cost: float = 0.0
    duration_s: float = 0.0
    error: str = ""
    at: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass(frozen=True)
class ReputationScore:
    """Evidence-based reputation for one agent."""

    agent_id: AgentId
    reliability: float
    success_rate: float
    total_outcomes: int
    avg_cost: float
    confidence: float

    def to_dict(self) -> dict:
        return {
            "agent_id": str(self.agent_id),
            "reliability": self.reliability,
            "success_rate": self.success_rate,
            "confidence": self.confidence,
            "total_outcomes": self.total_outcomes,
            "avg_cost": self.avg_cost,
        }


class ReputationLedger:
    """Append-only ledger of agent outcomes."""

    def __init__(self) -> None:
        self._outcomes: list[AgentOutcome] = []

    def record(self, outcome: AgentOutcome) -> None:
        self._outcomes.append(outcome)

    def outcomes_for(self, agent_id: AgentId) -> list[AgentOutcome]:
        return [o for o in self._outcomes if o.agent_id == agent_id]

    def all(self) -> list[AgentOutcome]:
        return list(self._outcomes)


class ReputationScorer:
    """Computes reputation from a ledger (deterministic, evidence-grounded)."""

    def __init__(self, ledger: ReputationLedger) -> None:
        self._ledger = ledger

    def score(self, agent_id: AgentId) -> ReputationScore:
        outcomes = self._ledger.outcomes_for(agent_id)
        if not outcomes:
            return ReputationScore(
                agent_id=agent_id,
                reliability=0.0,
                success_rate=0.0,
                total_outcomes=0,
                avg_cost=0.0,
                confidence=0.0,
            )
        n = len(outcomes)
        success = sum(1 for o in outcomes if o.success)
        reliability = self._reliability(outcomes)
        avg_cost = sum(o.cost for o in outcomes) / n
        confidence = min(1.0, n / 20.0)  # saturates after 20 recorded outcomes
        return ReputationScore(
            agent_id=agent_id,
            reliability=reliability,
            success_rate=success / n,
            total_outcomes=n,
            avg_cost=avg_cost,
            confidence=confidence,
        )

    @staticmethod
    def _reliability(outcomes: list[AgentOutcome]) -> float:
        """Exponential-weighted recent reliability (recent outcomes weigh more)."""
        total = 0.0
        weight_sum = 0.0
        for i, outcome in enumerate(reversed(outcomes[-50:])):
            weight = 0.9 ** i
            total += weight * (1.0 if outcome.success else 0.0)
            weight_sum += weight
        return total / weight_sum if weight_sum else 0.0
