# STATUS: aura-execution

## Architectural role
AUTHORITATIVE execution runtime for AURA. Owns the action lifecycle:
capability checks, permission & safety gates, approval review, budgets,
preparation, dispatch, observation, validation, recovery, flight-recorded
tracing. Security and approval gates are never bypassed.

## Canonical owner
`aura/src/aura/execution` (canonical runtime `aura/`) is the integrated
runtime. aura-execution is the standalone domain engine; it does NOT duplicate
`aura-execution-complete` (which is preserved as HISTORICAL — see below).

## Relationship to aura-execution-complete (boundary decision)
Both packages use the same top-level module name `aura_execution`, so they
cannot coexist in one interpreter. `aura-execution-complete` is the legacy
prototype and is preserved as HISTORICAL/SUPERSEDED. The authoritative runtime
is THIS package. No in-process bridge can exist; code that requires the legacy
interface must run against that repo in isolation.

## Implementation level
- Real authored files (src): 116 (37 preserved real modules + implemented
  missing modules/packages `__init__` tree)
- Scaffold/generated files: 0 (empty stub files in the old flat layout were
  superseded by real implementations in `src/aura_execution/`)
- Broken: 0

## Preserved real code
- `orchestration/orchestrator.py` (capability/permission/safety/budget gates,
  dispatch, observation, validation, recovery, flight-recorder events)
- `execution_state/*` (state machine + transition validation)
- `capabilities/*`, `permissions/*`, `safety/*`, `recovery/*`, `budgets/*`,
  `contracts/*`, `flight_recorder/*`, `tools/adapters/*`
- Real tests `tests/unit/test_state.py`, `tests/unit/test_vertical_slice.py`,
  `tests/security/test_safety_and_tools.py`, `tests/integration/test_pipeline.py`

## What is implemented (real behavior)
- Prop packaging into `src/aura_execution/` so imports work and tests run.
- `ExecutionEngine` (high-level) composing the orchestrator with:
  - timeout enforcement (`TimeoutGuard`)
  - cooperative cancellation (`CancellationToken`)
  - retries with explicit classification (transient vs permanent) —
    non-retryable failures are NEVER retried
  - idempotency (repeat with the same key returns the recorded outcome)
  - dry-run / simulation (never invokes the handler; no side effects)
  - rollback (LIFO undo from pre-registered callbacks)
  - compensation (only from explicitly pre-registered compensation actions)
- Capability matching (name + operation set, supports `*`).
- Validators: outcome success + expected-state match.
- Tool adapters (shell with allowlist, http, python-with-approved-executor,
  filesystem, database) with safe-fail semantics.
- Safety engine with ALLOW / REVIEW / DENY risk thresholds.

## Tests
- 26 passing. Covers: timeout, cancellation, retryable failure, non-retryable
  failure, idempotent repeat, approval rejection (REVIEW), dry run, rollback,
  compensation, missing capability (BLOCKED), high-risk review, expected-state
  mismatch, safety deny threshold, state-machine lifecycle, pipeline events.

## Validation gates
- Syntax compilation: PASS (ast parse over all 116 src files)
- Import validation: PASS (`from aura_execution import ExecutionEngine` works)
- Unit + integration tests: PASS (26 passed)
- Lint (ruff): PASS (exit 0)
- Type check (mypy): PASS (exit 0, run from parent dir to avoid repo-root
  `__init__.py` interference)
- Build/package check: NOT RUN (package not pip-installed in this session)

## Supported runtime status
- IMPORTED BY RUNTIME: No (standalone engine; canonical `aura/` integrates
  its own `aura.execution`)
- PRODUCTION READY: IMPLEMENTED (tested core + runtime guarantees; package
  install/build not yet exercised)

## Known limitations
- In-memory only: no durable checkpoint/replay store.
- Timeout enforcement is best-effort for synchronous handlers (cannot preempt
  a blocking call, only detect after completion).
- Retry classification is heuristic over error text.
