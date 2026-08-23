"""Cognitive loop: a bounded, state-machine-driven agent loop.

The loop composes the reasoning bridge, planning bridge, execution engine,
evaluation engine, recovery engine, loop controller, observation engine, and
flight recorder into one coherent cycle. It is NOT an uncontrolled while-loop:

- it has a maximum iteration count,
- it detects repetition/oscillation/stagnation via the loop controller,
- it terminates on hard denials (budget, safety, permission, constitution),
- it applies recovery per failure (retry/replan/escalate/abort),
- it is deterministic when its engines are deterministic.

Work context (plan, step index, retries) is owned by the loop and passed
explicitly through the state machine so the loop is re-entrant-safe.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from aura_agent.cognitive_loop.models import CognitiveStage, LoopOutcome
from aura_agent.contracts.errors import DomainError, LoopDetected
from aura_agent.execution_bridge.responses.execution_result import FailureClass

__all__ = ["CognitiveLoop", "CognitiveLoopSettings", "LoopWorkContext"]


@dataclass(frozen=True)
class CognitiveLoopSettings:
    """Bounded-loop configuration."""

    max_iterations: int = 20
    max_retries_per_step: int = 2


@dataclass
class LoopWorkContext:
    """Mutable working state for one loop run (no globals)."""

    plan: Any = None
    step_index: int = 0
    retries: int = 0
    observations: list = field(default_factory=list)
class CognitiveLoop:
    """Owns one goal-directed cognitive cycle set."""

    def __init__(
        self,
        *,
        execution_engine,
        planning_bridge,
        reasoning_bridge,
        observation_engine,
        evaluation_engine,
        recovery_engine,
        loop_controller,
        recorder=None,
        goal_engine=None,
        settings: CognitiveLoopSettings | None = None,
    ) -> None:
        self._execution = execution_engine
        self._planning = planning_bridge
        self._reasoning = reasoning_bridge
        self._observation = observation_engine
        self._evaluation = evaluation_engine
        self._recovery = recovery_engine
        self._loop = loop_controller
        self._recorder = recorder
        self._goals = goal_engine
        self._settings = settings or CognitiveLoopSettings()

    # ------------------------------------------------------------------ run
    def run(
        self,
        *,
        goal_id,
        agent_id,
        goal_description: str,
        world_state: dict[str, Any] | None = None,
        capabilities: list[str] | None = None,
    ) -> LoopOutcome:
        state = dict(world_state or {})
        capabilities = list(capabilities or [])
        ctx = LoopWorkContext()
        self._loop.reset()
        stage = CognitiveStage.OBSERVATION

        for iterations in range(1, self._settings.max_iterations + 1):
            # advance through ONE full cognitive cycle (OBSERVATION ->
            # ... -> REFLECTION -> back to OBSERVATION) or until the loop is
            # terminated. Each `iterations` tick is one complete cycle.
            cycle = 0
            while True:
                try:
                    stage = self._advance(
                        stage=stage,
                        goal_id=goal_id,
                        agent_id=agent_id,
                        goal_description=goal_description,
                        state=state,
                        capabilities=capabilities,
                        ctx=ctx,
                    )
                except LoopDetected as exc:
                    return LoopOutcome(
                        success=False,
                        reason=f"loop detected: {exc}",
                        iterations=iterations,
                    )
                except DomainError as exc:
                    return LoopOutcome(
                        success=False,
                        reason=f"domain stop: {exc}",
                        iterations=iterations,
                    )
                cycle += 1
                if stage is CognitiveStage.TERMINATED:
                    return LoopOutcome(
                        success=self._goal_succeeded(goal_id),
                        reason="cognitive loop terminated",
                        iterations=iterations,
                        result={
                            "final_state": state,
                            "plan_steps": self._plan_step_count(ctx),
                        },
                    )
                if stage is CognitiveStage.OBSERVATION:
                    break  # a full cycle completed; start the next iteration
                if cycle > len(CognitiveStage) + 2:  # safety net against a broken stage graph
                    break

        return LoopOutcome(
            success=False,
            reason=f"max iterations ({self._settings.max_iterations}) reached",
            iterations=self._settings.max_iterations,
            result={"final_state": state},
        )
# --------------------------------------------------------------- machinery
    def _advance(self, *, stage, goal_id, agent_id, goal_description, state, capabilities, ctx) -> CognitiveStage:
        """Execute one stage and return the next stage (or TERMINATED)."""
        if stage is CognitiveStage.OBSERVATION:
            self._observe(state, ctx)
            return CognitiveStage.INTERPRETATION

        if stage is CognitiveStage.INTERPRETATION:
            return CognitiveStage.REASONING

        if stage is CognitiveStage.REASONING:
            result = self._reasoning.reason(
                self._make_reasoning_request(goal_description, state, capabilities)
            )
            if result.answer == "request_approval":
                return self._terminate("escalated: reasoning requested approval")
            return CognitiveStage.PLANNING

        if stage is CognitiveStage.PLANNING:
            from aura_agent.planning_bridge import PlanningRequest

            plan = self._planning.plan(
                PlanningRequest(
                    goal=goal_description,
                    goal_id=goal_id,
                    agent_id=agent_id,
                    world_state=state,
                    capabilities=capabilities,
                )
            )
            if not plan.valid:
                return self._terminate(f"invalid plan: {'; '.join(plan.validation_errors)}")
            ctx.plan = plan
            ctx.step_index = 0
            ctx.retries = 0
            return CognitiveStage.DECISION

        if stage is CognitiveStage.DECISION:
            return CognitiveStage.EXECUTION

        if stage is CognitiveStage.EXECUTION:
            return self._do_execution(goal_id, agent_id, state, ctx)

        if stage is CognitiveStage.EVALUATION:
            return self._do_evaluation(goal_id, state, ctx)

        if stage is CognitiveStage.REFLECTION:
            self._record("reflection", {"signal": "iteration_complete"})
            return CognitiveStage.OBSERVATION

        return self._terminate("unknown stage reached")

    def _do_execution(self, goal_id, agent_id, state, ctx) -> CognitiveStage:
        if ctx.plan is None or ctx.step_index >= len(ctx.plan.steps):
            return self._terminate("plan exhausted without success")
        step = ctx.plan.steps[ctx.step_index]

        signature = f"{step.tool_name}:{tuple(sorted(step.inputs.items()))}"
        signals = self._loop.record(signature)
        if signals:
            raise LoopDetected("; ".join(f"{s.reason}: {s.detail}" for s in signals))

        from aura_agent.contracts.ids import ActionId
        from aura_agent.execution_bridge import ExecutionRequest
        from aura_agent.recovery import RecoveryRequest, RetryPolicy

        request = ExecutionRequest(
            action_id=ActionId.new(),
            tool_name=step.tool_name,
            capability=step.capability,
            agent_id=agent_id,
            goal_id=goal_id,
            inputs=dict(step.inputs),
            risk_score=0.1,
        )
        try:
            result = self._execution.execute(request)
        except DomainError:
            return self._terminate("hard denial during execution")

        if result.success:
            state.update(dict(step.expected_effects or {"completed": True}))
            ctx.step_index += 1
            ctx.retries = 0
            if ctx.step_index >= len(ctx.plan.steps):
                return CognitiveStage.EVALUATION
            return CognitiveStage.EXECUTION

        primary = result.primary
        failure_class = primary.failure_class if primary else None
        recovery = self._recovery.decide(
            RecoveryRequest(
                execution_id="exe-loop",
                goal_id=goal_id,
                tool_name=step.tool_name,
                failure_class=failure_class or FailureClass.UNKNOWN,
                attempts=ctx.retries,
                retry_policy=RetryPolicy(max_retries=self._settings.max_retries_per_step),
            )
        )
        self._record("recovery", {"strategy": recovery.strategy.value, "reason": recovery.reason})

        if recovery.should_retry:
            if ctx.retries < self._settings.max_retries_per_step:
                ctx.retries += 1
                return CognitiveStage.EXECUTION
            return self._terminate("retry budget exhausted for the step")

        if recovery.strategy.value == "replan":
            ctx.plan = None
            return CognitiveStage.REASONING

        return self._terminate(f"recovery: {recovery.reason}")

    def _do_evaluation(self, goal_id, state, ctx) -> CognitiveStage:
        from aura_agent.evaluation.models import StateExpectation

        expectations = [StateExpectation(path="goal_completed", expected=True)]
        eval_result = self._evaluation.evaluate(expectations, state)
        self._record("evaluation", {"verdict": eval_result.verdict.value, "mismatches": eval_result.mismatches})

        if self._goals is not None:
            try:
                if self._goals.evaluate_success(goal_id, state):
                    self._goals.mark_completed(goal_id)
                    return self._terminate("goal success criteria met")
            except KeyError:
                pass

        if not eval_result.mismatches:
            return self._terminate("expected state reached")
        return CognitiveStage.REFLECTION

    # --------------------------------------------------------------- helpers
    def _observe(self, state, ctx) -> None:
        observation = self._observation.observe(
            source="cognitive_loop",
            state=dict(state),
            signals=["iteration_complete"],
        )
        ctx.observations.append(observation)
        self._record("observation", {"state_keys": sorted(state), "n": len(ctx.observations)})

    def _record(self, event_type: str, payload: dict) -> None:
        if self._recorder is None:
            return
        from aura_agent.flight_recorder.events.agent_event import AgentEvent

        self._recorder.record(AgentEvent(event_type=event_type, payload=payload))

    def _make_reasoning_request(self, goal_description, state, capabilities):
        from aura_agent.reasoning_bridge import ReasoningRequest

        return ReasoningRequest(
            objective=f"pursue goal: {goal_description}",
            context={"state": state, "capabilities": capabilities},
        )

    @staticmethod
    def _terminate(message: str) -> CognitiveStage:
        return CognitiveStage.TERMINATED

    def _goal_succeeded(self, goal_id) -> bool:
        if self._goals is None:
            return False
        try:
            from aura_agent.goals.models.goal import GoalStatus
            return self._goals.get(goal_id).status is GoalStatus.COMPLETED
        except KeyError:
            return False

    @staticmethod
    def _plan_step_count(ctx) -> int:
        return len(ctx.plan.steps) if ctx.plan is not None else 0