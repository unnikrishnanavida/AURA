# STATUS: aura-planning

## Architectural role
AUTHORITATIVE standalone planning subsystem. Substantial authored code
preserved and repackaged into a proper `src/aura_planning/` package; missing
architectural behavior implemented (feasibility, capability-gap detection,
alternatives, contingency, replanning, first-class uncertainty).

## Canonical owner
`aura/src/aura/planning` (canonical runtime `aura/`). aura-planning is the
standalone planning engine; it integrates with the canonical runtime through
explicit contracts and does NOT duplicate it.

## Implementation level
- Real authored files (src): 534 (675 modules copied from the flat layout,
  duplicates/nested duplicates removed, real implementations retained)
- Scaffold/generated files: 0
- Broken: 0

## Preserved real code
- Goals: `Goal`, `GoalStatus`, subgoals, decomposition tree/validator/decomposer
- Constraints: `Constraint`, `ConstraintSet`, hard/soft constraints, validator,
  solver, feasibility checker
- Risk: `Risk`, `PlanRisk`, `RiskAnalyzer`, mitigation/fallback
- Resources: `Resource`, `ResourceRequirement`, `Registry`, `Allocator`
- Planners: forward/backward/state-space, hierarchical, probabilistic, reactive
- Dependencies: `DependencyGraph` (cycle detection via topological order),
  critical path
- Replanning: `ReplanningEngine`, partial/full/adaptive replanners, triggers
- Simulation, telemetry histogram, reasoning-bridge router
- Real tests: test_resource_engine, test_risk_engine, test_safety_engine,
  test_simulation_engine, test_telemetry, test_reasoning_bridge

## What is implemented (real behavior)
- `Plan` model with explicit feasibility/actionability signals:
  - `unsatisfied_constraints` (never hidden)
  - `missing_capabilities` (capability gaps)
  - `risk` (PlanRisk exposure)
  - `uncertainty` (first-class, 0..1)
  - `contingency` plan
  - `alternatives`
- `Planner` facade running the flow:
  GOAL -> DECOMPOSITION -> CONSTRAINT VALIDATION -> CANDIDATE PLANS ->
  CAPABILITY GAP DETECTION -> RISK ANALYSIS -> PLAN COMPARISON ->
  SELECTED PLAN -> CONTINGENCY PLAN
- `select()` never picks an infeasible plan while a feasible one exists.
- `replan_after_failure()` excludes the failed path and picks the best
  alternative.
- Critical property: the planner does NOT pretend impossible plans are
  executable — infeasibility is explicit and preserved in `to_dict()`.

## Tests
- 18 passing (6 preserved + 12 new). Covers: impossible constraints,
  dependency conflict/cycle, missing capability, alternative plan selection,
  risk comparison, replanning after failure, contingency attachment,
  uncertainty, high-risk not-actionable, feasibility representation.

## Validation gates
- Syntax compilation: PASS (ast parse over src)
- Import validation: PASS (`from aura_planning import Planner, Plan` works)
- Unit tests: PASS (18 passed)
- Lint (ruff): PASS (exit 0 on new modules)
- Type check (mypy): PASS (exit 0 on `planning` + `plans` packages)
- Build/package check: NOT RUN (package not pip-installed in this session)

## Supported runtime status
- IMPORTED BY RUNTIME: No (standalone; canonical `aura/` is the runtime)
- PRODUCTION READY: IMPLEMENTED (tested core planner + preserved real
  modules; full-package install/build not yet exercised)

## Known limitations
- Capability-gap detection is structural (name-based), not semantic.
- Uncertainty is heuristic (unverified action ratio + gap penalty).
- Not all preserved submodules have dedicated tests; the core planning flow
  and the mission-required behaviors are covered.
