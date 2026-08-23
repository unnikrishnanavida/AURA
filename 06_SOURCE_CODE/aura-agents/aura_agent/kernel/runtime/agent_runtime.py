"""Agent runtime: wired composition of all engine domains.

The runtime is the *composition root*. Every dependency is injected through
the constructor (no global singletons), enabling deterministic tests,
replacement of providers, and multi-agent isolation. The runtime exposes a
small, stable set of operations: run a goal (cognitive loop), execute a single
action (guarded pipeline), reflect, and report diagnostics.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from aura_agent.contracts.ids import AgentId, GoalId
from aura_agent.goals.models.goal import Goal

__all__ = ["AgentRuntime", "RuntimeComponents", "RuntimeDiagnostics"]


@dataclass
class RuntimeComponents:
    """The injectable component set of an agent runtime."""

    goal_engine: Any
    execution_engine: Any
    cognitive_loop: Any
    observation_engine: Any
    evaluation_engine: Any
    flight_recorder: Any
    genome: Any
    reasoning_bridge: Any = None
    planning_bridge: Any = None
    recovery_engine: Any = None
    memory_bridge: Any = None
    learning_bridge: Any = None
    telemetry: Any = None
    logger: Any = None
    loop_controller: Any = None
    budget_engine: Any = None
    capability_registry: Any = None
    tool_registry: Any = None
    reputation_engine: Any = None


@dataclass
class RuntimeDiagnostics:
    """A snapshot of runtime health and behavior counters."""

    healthy: bool
    goals: list[dict]
    executions: list[dict]
    telemetry: dict = field(default_factory=dict)


class AgentRuntime:
    """The composed agent runtime (the only entry point application code needs)."""

    def __init__(
        self,
        agent_id: AgentId,
        identity: Any,
        components: RuntimeComponents,
    ) -> None:
        self.agent_id = agent_id
        self.identity = identity
        self.components = components
        self._goals: list[GoalId] = []
        if components.logger is not None:
            components.logger.info("runtime.ready", agent_id=str(agent_id))

    # -- goal operations ----------------------------------------------------------
    def create_goal(
        self,
        *,
        description: str,
        success_criteria: list[str] | None = None,
        constraints: list | None = None,
    ) -> Goal:
        goal = self.components.goal_engine.create_goal(
            agent_id=self.agent_id,
            description=description,
            success_criteria=success_criteria,
            constraints=constraints,
        )
        self._goals.append(goal.id)
        return goal

    def run_goal(
        self,
        *,
        goal: Goal,
        world_state: dict | None = None,
        capabilities: list[str] | None = None,
    ) -> Any:
        """Execute a goal end-to-end through the cognitive loop."""
        self.components.goal_engine.activate(goal.id)
        outcome = self.components.cognitive_loop.run(
            goal_id=goal.id,
            agent_id=self.agent_id,
            goal_description=goal.description,
            world_state=world_state or {},
            capabilities=capabilities or [],
        )
        if self.components.telemetry is not None:
            self.components.telemetry.finish_execution(
                agent_id=str(self.agent_id),
                success=outcome.success,
                duration_s=0.0,
            )
        return outcome

    def execute_action(self, request: Any) -> Any:
        """Run a single action through the guarded execution pipeline."""
        result = self.components.execution_engine.execute(request)
        memory = self.components.memory_bridge
        if memory is not None:
            memory.write_outcome(
                actor=str(self.agent_id),
                action=request.tool_name,
                succeeded=result.success,
                correlation_id=str(result.execution_id),
            )
        return result
