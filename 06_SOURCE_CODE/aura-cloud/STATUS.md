# STATUS: aura-cloud

## Architectural role
AUTHORITATIVE cloud abstraction + SIMULATION runtime. Provider protocols,
deployment contracts, cost budgets, rollback, deployment audit.

## Canonical owner
aura-cloud (no canonical duplicate in `aura/`).

## Implementation level
- Real authored files (src): 6 (contracts, simulator, engine, models, budget,
  rollback, audit ledger)
- Scaffold/generated files: 0 (all tiny 2-5-line stub files removed)
- Broken: 0

## What is implemented (real behavior, honestly labeled)
- `CloudProvider` protocol + `BaseCloudProvider` interface. Real providers
  MUST override `deploy`; the interface raises `NotImplementedError` rather
  than pretending to deploy.
- `SimulatedProvider` — explicitly labeled `kind="simulation"`; every result
  is truthful (can inject deploy failures; never fakes success).
- `CloudControlPlane.plan()` — capability-gap enforcement + risk-budget
  guardrail (rejects missing capabilities and high-risk deployments).
- `CostBudget` (cost ceiling with truthful charge/allow) and `CostEstimate`.
- `RollbackLedger` (append-only per-plan rollback records).
- `DeploymentAudit` (append-only deployment events: planned/deployed/
  rolled_back).

## Explicit non-claims
- NO real AWS deployment.
- NO real Azure deployment.
- NO real GCP deployment.
- No provider SDK integration exists in this repo; any real-provider work must
  land behind an adapter implementing `CloudProvider` with `kind="real"`.

## Tests
- 13 passing. Covers: simulation labeling, capability-gap rejection, high-risk
  rejection, truthful deploy+rollback, injected deploy failure, interface
  provider not pretending to deploy, budget ceiling, negative-cost rejection,
  rollback ledger, deployment audit trail.

## Validation gates
- Syntax compilation: PASS
- Import validation: PASS (`from aura_cloud import SimulatedProvider` works)
- Unit tests: PASS (13 passed)
- Lint (ruff): PASS (exit 0)
- Type check (mypy): NOT RUN (flat-layout; not configured in this session)
- Build/package check: NOT RUN

## Supported runtime status
- IMPORTED BY RUNTIME: No (standalone)
- PRODUCTION READY: INTERFACE + SIMULATION (no real cloud deployment claimed)

## Known limitations
- No real provider SDK integration.
- The engine is in-memory and process-local.
