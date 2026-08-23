"""Telemetry metrics: counters and gauges for runtime observability.

This is a dependency-free metrics collector aligned with the AURA telemetry
domains: executions, success/failure, retries, recovery, latency, budget
consumption, safety/permission denials, and loop detections.
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from datetime import UTC, datetime

__all__ = ["AgentMetrics", "TelemetryCollector"]


@dataclass
class AgentMetrics:
    """Atomic counters for one agent runtime."""

    executions: int = 0
    successes: int = 0
    failures: int = 0
    retries: int = 0
    recoveries: int = 0
    loop_detections: int = 0
    safety_denials: int = 0
    permission_denials: int = 0
    tool_failures: int = 0
    total_duration_s: float = 0.0
    budget_exceeded: int = 0
    last_event_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    def finish(self, *, success: bool, duration_s: float) -> None:
        self.executions += 1
        self.total_duration_s += duration_s
        if success:
            self.successes += 1
        else:
            self.failures += 1
        self.last_event_at = datetime.now(UTC)

    def success_rate(self) -> float:
        if self.executions == 0:
            return 0.0
        return self.successes / self.executions

    def snapshot(self) -> dict:
        return {
            "executions": self.executions,
            "successes": self.successes,
            "failures": self.failures,
            "success_rate": self.success_rate(),
            "retries": self.retries,
            "recoveries": self.recoveries,
            "loop_detections": self.loop_detections,
            "safety_denials": self.safety_denials,
            "permission_denials": self.permission_denials,
            "tool_failures": self.tool_failures,
            "budget_exceeded": self.budget_exceeded,
            "avg_duration_s": (
                self.total_duration_s / self.executions if self.executions else 0.0
            ),
        }


class Telemetry:
    """Collects metrics for one runtime (or all agents when ``_global``)."""

    def __init__(self, *, per_agent: bool = True) -> None:
        self._per_agent = per_agent
        self._agents: dict[str, AgentMetrics] = defaultdict(AgentMetrics)

    def for_agent(self, agent_id: str) -> AgentMetrics:
        if not self._per_agent:
            return self._agents["_all"]
        return self._agents[str(agent_id)]

    def finish_execution(
        self, *, agent_id: str, success: bool, duration_s: float
    ) -> None:
        self.for_agent(agent_id).finish(success=success, duration_s=duration_s)

    def increment(self, *, agent_id: str, metric: str, amount: int = 1) -> None:
        metrics = self.for_agent(agent_id)
        if hasattr(metrics, metric):
            setattr(metrics, metric, getattr(metrics, metric) + amount)

    def snapshot(self, agent_id: str | None = None) -> dict:
        if agent_id is not None:
            return self.for_agent(agent_id).snapshot()
        return {
            str(aid): m.snapshot() for aid, m in sorted(self._agents.items())
        }

    def reset(self) -> None:
        self._agents.clear()