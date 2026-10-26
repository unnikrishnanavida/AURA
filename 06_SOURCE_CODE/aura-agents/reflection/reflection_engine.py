"""Reflection engine: analyzes outcomes and produces improvement signals.

Reflection ONLY analyzes and emits signals. It never directly modifies safety
policies, permission policies, constitutional rules, security boundaries, or
core runtime invariants -- signals targeting those areas are flagged
``is_safety_relevant()`` and must be authorized by an explicit mechanism
before any learning may consume them.
"""

from __future__ import annotations

from aura_agent.contracts.ids import AgentId
from aura_agent.execution_bridge.responses.execution_result import ExecutionResult
from aura_agent.reflection.models import (
    ImprovementSignal,
    Reflection,
    ReflectionSeverity,
    ReflectionTarget,
)

__all__ = ["ReflectionEngine"]

#: local alias so the engine reads naturally
ReflectionSignal = ImprovementSignal


class ReflectionEngine:
    """Produces deterministic reflection signals from execution results."""

    def reflect(self, result: ExecutionResult, *, agent_id: AgentId) -> Reflection:
        signals: list[ImprovementSignal] = []
        summary_parts: list[str] = []
        targeted: list[ReflectionTarget] = []
        primary = result.primary

        if result.success:
            targeted.append(ReflectionTarget.OUTCOME)
            summary_parts.append(f"execution {result.execution_id} succeeded")
            if primary is not None and primary.output:
                signals.append(
                    ReflectionSignal(
                        signal_type="strategy.improvement",
                        target=primary.tool_name,
                        suggestion="repeat the same tool for identical goals",
                        evidence={"output": primary.output},
                    )
                )
        else:
            targeted.append(ReflectionTarget.FAILURE)
            failure_name = (
                primary.failure_class.value
                if primary is not None and primary.failure_class
                else "unknown"
            )
            summary_parts.append(
                f"execution {result.execution_id} failed with {failure_name}"
            )
            if failure_name in {"timeout", "resource"}:
                signals.append(
                    ReflectionSignal(
                        signal_type="strategy.improvement",
                        target=primary.tool_name if primary else "",
                        suggestion="raise tool timeout or pre-allocate budget",
                        severity=ReflectionSeverity.WARNING,
                        evidence={"failure_class": failure_name},
                    )
                )

        if primary is not None and primary.duration_s > 0:
            targeted.append(ReflectionTarget.EFFICIENCY)
            signals.append(
                ReflectionSignal(
                    signal_type="efficiency.timing",
                    target=primary.tool_name,
                    suggestion=f"observed duration {primary.duration_s:.3f}s",
                    severity=ReflectionSeverity.INFO,
                    evidence={"duration_s": primary.duration_s},
                )
            )

        return Reflection(
            execution_id=result.execution_id,
            agent_id=agent_id,
            goal_id=None,
            targets=targeted,
            summary="; ".join(summary_parts) or "no reflection content",
            signals=signals,
        )
