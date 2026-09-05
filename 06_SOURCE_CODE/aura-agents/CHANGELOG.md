# Changelog

All notable changes to AURA Agent are documented here.

## [0.1.0] - 2026-08-23

### Added

- **Core contracts** (`contracts/`): namespaced IDs, typed domain exceptions,
  explicit execution-state machine with recorded transitions, and
  dependency-injection protocols.
- **Capability discovery**: deterministic registry with scopes, wildcard
  matching, availability, diagnostics, and agent-capability discovery.
- **Guarded execution pipeline** (`execution_bridge/`): capability ->
  permission -> constitution -> safety -> autonomy -> budget -> dispatch ->
  validation with flight-recorder events at each stage.
- **Goals**: lifecycle, priorities, constraints, success criteria, conflict
  detection, and deterministic decomposition with dependencies.
- **Policies**: default-deny permission engine (specificity + deny-wins) and a
  safety evaluator with explicit coverage/review semantics (uncovered
  medium+ risk -> REVIEW).
- **Constitution**: hard, non-bypassable principles that autonomy can never
  overturn.
- **Autonomy**: four ordered modes (MANUAL/ASSISTED/SUPERVISED/AUTONOMOUS),
  approval policies, and authorization-gated mode transitions.
- **Budgets**: multidimensional (time/actions/cost) accounting with atomic
  consumption.
- **Tools**: schema-validated tools, registry, and a process sandbox with
  timeouts and guarded fragments.
- **Recovery**: single-authority failure classification and strategy decision
  (retry/fallback/compensate/rollback/replan/escalate/abort) with bounded
  retries.
- **Loop control**: repetition, oscillation, and stagnation detection.
- **Cognitive loop**: bounded OBSERVATION->...->REFLECTION state machine
  composing reasoning/planning/execution/evaluation/recovery.
- **Bridges**: provider-independent reasoning and planning, plus memory and
  learning bridges with validated-signal gates.
- **Flight recorder / provenance / replay**: append-only event store,
  causal-chain reconstruction, and read-only trajectory reconstruction.
- **Reflection / genome / learning**: outcome analysis, versioned attributable
  learned behavior, and safety-refusing learning gate.
- **Delegation / multi-agent / reputation**: capability- and reputation-gated
  task hand-off, message bus, coordinator, evidence-based reputation.
- **Telemetry / configuration**: per-agent counters, secret-redacting
  structured logging, typed dev/production/research profiles.
- **Public API**: `AgentBuilder` DSL, `AgentRuntime` composition root.
- **92 tests**: unit, integration, contract, and end-to-end scenario coverage
  including failure injections.

### Validation

- `mypy` clean, `ruff` clean, no circular imports (102 modules),
  security audit passing, config validation passing.
- Examples: `basic_agent.py`, `delegation_multi_agent.py` run successfully.

### Notes / INTERFACE READY

- Real AURA Reasoning/Planning/Memory engine adapters are represented by
  protocols; deterministic built-ins run offline until the sibling engines are
  installed (`INTERFACE READY / IMPLEMENTATION PENDING`).