# AURA Agent

An autonomous-agent runtime for the AURA ecosystem: goals, guarded action
execution, safety, autonomy, budgets, recovery, a bounded cognitive loop,
flight recording, provenance/replay, reflection-driven learning, delegation,
multi-agent coordination, reputation, telemetry, and configuration.

This package is the **Agent engine** in the AURA system. It does **not**
reimplement AURA Core, Brain, Reasoning, Memory, Learning, or SDK â€” it
integrates with those engines through stable adapter interfaces.

---

## Architecture

The runtime is organized into cohesive domains. Each domain owns exactly one
responsibility and is consumed through injected interfaces â€” no global
singletons.

| Domain                  | Responsibility                                             |
| ----------------------- | ---------------------------------------------------------- |
| `contracts/`            | canonical IDs, domain exceptions, execution states         |
| `goals/`                | goal lifecycle, decomposition, conflicts, success criteria |
| `capability_discovery/` | deterministic capability registry + agent discovery        |
| `policies/`             | permission engine (default-deny) and safety evaluator       |
| `constitution/`         | hard behavioral boundaries (never auto-amended)             |
| `autonomy/`             | autonomy modes + approval policies                           |
| `budgets/`              | multidimensional budget accounting                          |
| `tools/`                | controlled tools, tool registry, process sandbox            |
| `execution_bridge/`     | guarded execution pipeline                                  |
| `observation/`          | recorded observations of actual world state                 |
| `evaluation/`           | expected-vs-observed evaluation and goal progress           |
| `recovery/`             | single-authority failure classification + recovery strategy |
| `loop_control/`         | repetition/oscillation/stagnation detection                 |
| `cognitive_loop/`       | bounded OBSERVATION->...->REFLECTION state machine          |
| `reasoning_bridge/`     | provider-independent reasoning contract                     |
| `planning_bridge/`      | goal -> validated executable plan                           |
| `flight_recorder/`      | append-only event trajectory                                |
| `provenance/`           | causal chain reconstruction from recorded events            |
| `replay/`               | read-only trajectory/state reconstruction                   |
| `reflection/`           | outcome analysis producing improvement signals              |
| `learning_bridge/`      | validated-signal gate into the genome                       |
| `genome/`               | versioned, attributable learned behavior + performance      |
| `memory_bridge/`        | episodic/semantic/experience retrieval via injected provider|
| `delegation/`           | capability + reputation-gated task hand-off                 |
| `multi_agent/`          | message bus, coordinator, shared goals                      |
| `reputation/`           | evidence-based reliability/success scoring                  |
| `telemetry/`            | counters and secret-redacting structured logs               |
| `configuration/`        | typed dev/production/research profiles                      |
| `kernel/`               | the composed `AgentRuntime`                                 |
| `dsl`                   | thin public `AgentBuilder` facade                            |

## Quick start

```python
from aura_agent import dsl
from aura_agent.tools import Tool

def handler(inputs, *, context):
    return {"completed": True}

agent = (
    dsl.AgentBuilder(name="demo")
    .with_tool(Tool(name="tools.finalize", description="finish",
                    input_schema={}, capability="tools.finalize",
                    permissions=(), handler=handler))
    .allow(action="tools.*", resource="*")
    .with_capability("tools.finalize")
    .build()
)

goal = agent.create_goal("finalize", success_criteria=["completed == True"])
outcome = agent.run_goal(goal=goal, capabilities=["tools.finalize"])
print(outcome.success)  # True
```

## Execution pipeline

Every `ExecutionRequest` passes the guarded pipeline in a fixed order:

```
request validation
  -> capability match
  -> permission decision (default-deny)
  -> constitution check
  -> safety evaluation
  -> autonomy/approval gate
  -> budget check
  -> tool dispatch (sandbox boundary)
  -> result validation
  -> state machine transition
  -> flight-recorder event
```

No subsystem can override a hard denial from an earlier stage: an
`AUTONOMOUS` agent still cannot execute a safety-`DENY`, a permission-`DENY`,
a constitution-`DENY`, or an exhausted budget.
## Safety model

- Explicit SafetyPolicy entries with orbidden_capabilities, 
eview_capabilities, and covered_capabilities.
- Uncovered capabilities at medium+ risk default to REVIEW (a human gate), never silent allow or silent deny.
- Autonomy never converts a DENY into an ALLOW.

## Autonomy model

MANUAL < ASSISTED < SUPERVISED < AUTONOMOUS. Increasing autonomy only raises the risk threshold that may auto-approve; it never disables a hard boundary. Escalating autonomy requires an authorizing entity.

## Recovery model

Failures are classified and one recovery engine decides the strategy (RETRY, FALLBACK, COMPENSATE, ROLLBACK, REPLAN, ESCALATE, ABORT). Retry is bounded by RetryPolicy.

## State machine

PENDING -> READY -> RUNNING -> SUCCEEDED/FAILED/CANCELLED/ROLLED_BACK plus WAITING, BLOCKED, RECOVERING. Invalid transitions raise InvalidStateTransition; every transition is recorded.

## AURA engine integration

Sibling engines (when installed) are consumed through their public contract; otherwise the adapter protocols in contracts/interfaces.py define the boundary and deterministic built-in implementations run offline (rule-based reasoning, goal-refinement planning, in-memory memory, validated-signal learning gate).

Real sibling-engine adapters are marked **INTERFACE READY / IMPLEMENTATION PENDING** until the corresponding AURA engine is installed.

## Testing
```bash
`ash
python -m pytest tests              # unit + integration + contract + e2e
python scripts/validate_imports.py  # circular-import check
python scripts/validate_config.py   # configuration validation
python scripts/security_check.py    # security audit
python -m mypy aura_agent           # type checking
python -m ruff check aura_agent     # linting
```

The e2e scenario drives goal -> plan -> capability -> permission -> safety -> budget -> tool -> result -> evaluation -> recorder, then injects missing capability, permission denial, approval required, tool failure, timeout, budget exhaustion, and repeated-failure loop detection.

## Examples

- examples/basic_agent.py â€” build an agent, execute an action, run a goal
- examples/delegation_multi_agent.py â€” reputation-based delegation and multi-agent coordination

## Security

See SECURITY.md. The process sandbox refuses known-dangerous command fragments, never spawns a real shell, input schemas reject unknown keys, and logs redact secrets.
