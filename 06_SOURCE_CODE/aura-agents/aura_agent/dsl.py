"""Public DSL: minimal ergonomic entry points for end users.

``AgentBuilder`` wires a full default agent runtime from a few options and
returns an :class:`~aura_agent.kernel.runtime.agent_runtime.AgentRuntime`.
The DSL is deliberately thin: it is composition only, never domain logic.
"""

from __future__ import annotations

from aura_agent.autonomy import AutonomyEngine, AutonomyMode
from aura_agent.budgets import BudgetEngine
from aura_agent.capability_discovery import Capability, CapabilityRegistry
from aura_agent.cognitive_loop import CognitiveLoop, CognitiveLoopSettings
from aura_agent.constitution import AgentConstitution
from aura_agent.contracts.ids import AgentId
from aura_agent.evaluation import EvaluationEngine
from aura_agent.execution_bridge import ExecutionDependencies, ExecutionEngine
from aura_agent.flight_recorder import AgentFlightRecorder
from aura_agent.genome import AgentGenome
from aura_agent.goals import GoalEngine
from aura_agent.identity import AgentIdentity, AgentVersion, IdentityRegistry
from aura_agent.kernel.runtime.agent_runtime import AgentRuntime, RuntimeComponents
from aura_agent.learning_bridge import LearningBridge
from aura_agent.loop_control import LoopController
from aura_agent.memory_bridge import InMemoryMemory, MemoryBridge
from aura_agent.observation import ObservationEngine
from aura_agent.planning_bridge import GoalRefinementPlanner, PlanningBridge
from aura_agent.policies import Decision, PermissionPolicy, PolicyEngine
from aura_agent.policies.safety import SafetyEvaluator
from aura_agent.reasoning_bridge import ReasoningBridge
from aura_agent.recovery import RecoveryEngine
from aura_agent.reflection import ReflectionEngine
from aura_agent.telemetry import AgentLogger, Telemetry
from aura_agent.tools import ToolRegistry

__all__ = ["AgentBuilder", "default_agent"]
class AgentBuilder:
    """Composes a default agent runtime with conservative safe defaults."""

    def __init__(
        self, *, agent_id: AgentId | None = None, name: str = "aura-agent"
    ) -> None:
        self._agent_id = agent_id or AgentId.new()
        self._name = name
        self._autonomy_mode = AutonomyMode.SUPERVISED
        self._max_iterations = 20
        self._initial_capabilities: list[str] = []
        self._tools: list = []
        self._allow = False
        self._allow_action = "*"
        self._allow_resource = "*"

    # -- hooks -----------------------------------------------------------------
    def with_autonomy(self, mode: AutonomyMode) -> "AgentBuilder":
        self._autonomy_mode = mode
        return self

    def with_capability(self, name: str) -> "AgentBuilder":
        self._initial_capabilities.append(name)
        return self

    def with_tool(self, tool) -> "AgentBuilder":
        self._tools.append(tool)
        return self

    def allow(self, *, action: str, resource: str = "*") -> "AgentBuilder":
        """Explicitly permit an action family; default stays deny."""
        self._allow = True
        self._allow_action = action
        self._allow_resource = resource
        return self

    def build(self) -> AgentRuntime:
        """Assemble and return a fully wired agent runtime."""
        agent_id = self._agent_id

        # tool + capability registries
        tool_registry = ToolRegistry()
        for tool in self._tools:
            tool_registry.register(tool)

        caps = CapabilityRegistry()
        for cap in self._initial_capabilities:
            caps.register(Capability(name=cap))
        for tool in self._tools:
            if not caps.has(tool.capability):
                caps.register(Capability(name=tool.capability))

        # permission engine: default-deny, explicit allow rules
        policies = PolicyEngine()
        policies.add_policy(
            PermissionPolicy(
                name="base-deny",
                effect=Decision.DENY,
                action="*",
                resource="*",
            )
        )
        if self._allow:
            policies.add_policy(
                PermissionPolicy(
                    name="explicit-allow",
                    effect=Decision.ALLOW,
                    action=self._allow_action,
                    resource=self._allow_resource,
                )
            )

        # engines and services ------------------------------------------------
        safety = SafetyEvaluator(review_uncovered_risk=0.5)
        autonomy = AutonomyEngine(initial_mode=self._autonomy_mode)
        budgets = BudgetEngine()
        constitution = AgentConstitution()
        recorder = AgentFlightRecorder()
        logger = AgentLogger(name=self._name)

        reasoning = ReasoningBridge()
        planning = PlanningBridge(provider=GoalRefinementPlanner())
        evaluation = EvaluationEngine()
        observation = ObservationEngine()
        recovery = RecoveryEngine()
        loop_controller = LoopController()
        goal_engine = GoalEngine()
        genome = AgentGenome(agent_id)
        telemetry = Telemetry()
        memory = MemoryBridge(provider=InMemoryMemory())
        learning = LearningBridge(genome=genome, authorize_safety_relevant=False)

        execution = ExecutionEngine(
            deps=ExecutionDependencies(
                tool_registry=tool_registry,
                capability_registry=caps,
                policy_engine=policies,
                constitution_checker=constitution,
                safety_evaluator=safety,
                autonomy_engine=autonomy,
                budget_engine=budgets,
                recorder=recorder,
            )
        )

        loop = CognitiveLoop(
            execution_engine=execution,
            planning_bridge=planning,
            reasoning_bridge=reasoning,
            observation_engine=observation,
            evaluation_engine=evaluation,
            recovery_engine=recovery,
            loop_controller=loop_controller,
            recorder=recorder,
            goal_engine=goal_engine,
            settings=CognitiveLoopSettings(max_iterations=self._max_iterations),
        )

        identity = AgentIdentity(
            agent_id=agent_id, name=self._name, version=AgentVersion()
        )

        components = RuntimeComponents(
            goal_engine=goal_engine,
            execution_engine=execution,
            cognitive_loop=loop,
            observation_engine=observation,
            evaluation_engine=evaluation,
            flight_recorder=recorder,
            genome=genome,
            reasoning_bridge=reasoning,
            planning_bridge=planning,
            recovery_engine=recovery,
            memory_bridge=memory,
            learning_bridge=learning,
            telemetry=telemetry,
            logger=logger,
            loop_controller=loop_controller,
        )

        return AgentRuntime(
            agent_id=agent_id, identity=identity, components=components
        )


def default_agent(*, name: str = "aura-agent") -> AgentRuntime:
    """Build a default agent with no tools/capabilities (safe by default)."""
    return AgentBuilder(name=name).build()