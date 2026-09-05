# AURA ECOSYSTEM ARCHITECTURE

## Vision
AURA (Autonomous Universal Reasoning Architecture) is an intelligence-infrastructure platform, not a
chatbot. It coordinates memory, knowledge, reasoning, research, planning, execution, agents, learning,
and reflection behind a unified, safety-bounded orchestration layer.

## High-level lifecycle

    INPUT -> OBSERVATION -> INTERPRETATION -> MEMORY -> KNOWLEDGE -> REASONING -> RESEARCH
      -> PLANNING -> DECISION -> EXECUTION -> SECURITY -> OBSERVATION -> EVALUATION
      -> REFLECTION -> LEARNING -> VALIDATED IMPROVEMENT -> NEXT CYCLE

## Runtime topology (canonical = 06_SOURCE_CODE/aura)

The integrated `aura/` package is the ONE authoritative platform. It is a flat package with domain
subpackages and no circular dependency across domains:

    foundation/   ids, errors, Result, clocks, lifecycle, cancellation, RNG, validation, serialization
    config/       typed settings + layered loader (defaults -> file -> env)
    core/         bootstrap, DI container, registry, lifecycle manager, health/readiness
    memory/       working/episodic/semantic/procedural, provenance, confidence, graph, consolidation
    knowledge/    claim/evidence/source, trust model, verification, contradiction detection
    reasoning/    deductive/abductive/causal/probabilistic/counterfactual/analogical + consensus/verification
    research/     epistemic ledger, claim passport, evidence provenance, hypotheses
    planning/     decomposition, constraints, risk analysis, plan comparison
    execution/    action models, world-state vs action-input separation, idempotency, checkpoint
    reflection/   post-execution review, counterfactual reflection
    learning/     validated signal gate, versioned registry, rollback, safety-authorization
    brain/        cognitive orchestration wiring the full lifecycle (bounded loops)
    security/     capabilities, default-deny permissions, safety, autonomy, budgets, recovery,
                  audit, redaction, adaptive defense (sandbox + approval + canary + rollback)
    observability/ logging, metrics, flight recorder, replay, provenance graph
    providers/    provider profiles/registry + embedded deterministic provider
    sdk/          `from aura import Aura` typed client
    api/          HTTP service (health/ready/reason/replay/openapi) - thin routes
    cli/          aura health | run | reason | plan | replay | security status | version | config validate
    agents/       bridge to the guarded aura-agents runtime (optional extra)

## Standalone repositories: role

Several standalone trees under `06_SOURCE_CODE/` are STRONG, tested engines that the integrated platform
orchestrates or mirrors:

- `aura-agents`      guarded agent runtime (92 tests pass) -> bridged by `aura/agents`
- `aura-research`    research engine (tests pass)         -> mirrored by `aura/research`
- `aura-reasoning`(2)/`aura_reasoning` historical reasoning reference (see consolidation plan)
- `aura-execution-complete` controlled execution engine
- `aura-security`    adaptive-defense lifecycle (sandbox/approval/canary/rollback), tests pass

The remaining standalone trees (`aura-api`, `aura-core`, `aura-memory`, `aura-knowledge`, `aura-planning`,
`aura-cloud`, `aura-desktop`, `aura-mobile`, etc.) are scaffolds or auto-generated trees. Per the
mission rules (quality > file count; one authoritative implementation), the canonical implementations live
in the integrated `aura/` package, and the standalone trees are documented as PARTIAL/SCAFFOLD/HISTORICAL,
not regenerated as fake code.

## Safety & security architecture

- Default-deny permissions, capability-based execution, safety ALLOW/REVIEW/DENY, approval gates.
- Multi-dimensional budgets (actions/cost/tokens/time/api-calls).
- Learning gate: OBSERVATION -> CANDIDATE SIGNAL -> VALIDATION -> APPROVED SIGNAL -> CONTROLLED UPDATE;
  safety-relevant signals require explicit authorization and support rollback.
- Adaptive defense: DETECT -> EVIDENCE -> CLASSIFY -> CONTROL-GAP -> DEFENSE SELECTION ->
  REMEDIATION SPEC -> TESTS -> SANDBOX VALIDATION -> REGRESSION -> APPROVAL GATE -> CANARY ->
  HEALTH MONITOR -> ROLLBACK. Generated code is never auto-deployed to production.
- Flight recorder + replay with explicit RECORDED vs RECONSTRUCTED state; provenance graph.

## Integration boundaries

- SDK/API/CLI are thin clients; all domain logic lives in services.
- Brain coordinates engines; no engine is a god-object; loops are bounded (max iterations, timeout,
  cancellation, stagnation detection).
- Persistence is behind interfaces (in-memory for tests; adapters for future SQLite/Postgres/Redis).
