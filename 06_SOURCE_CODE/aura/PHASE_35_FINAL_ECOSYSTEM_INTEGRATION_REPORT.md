# Phase 35 — Final Ecosystem Integration Report

**Status:** COMPLETE (integration scenarios, performance baseline, docs,
hygiene). Commit: `chore(phase35)`. Full suite **419/419** passed (RC 0) with
live PostgreSQL 18 in the final gate.

---

## 1. End-to-end scenarios (A–G) — `tests/e2e/test_scenarios.py` (7 tests, all pass)

| Scenario | Proof |
|----------|-------|
| A simple question | auth-gated flow → Brain → Reasoning → **provider boundary** (safe synthesis) → response → audit; `provider_call=1`, `execution_count>=1` |
| B memory | write → **new session over the same SQLite store** → retrieval |
| C evidence→answer | fact+rule → answer ≠ "I do not know", recorded in the flight recorder (provenance), `execution_id` present |
| D task | `planning.plan(...)` produced a plan; PolicyEngine **default-deny** without a rule, ALLOW with explicit rule |
| E security event | brute-force signal → `ThreatMonitor` → HIGH **incident** → audit trail |
| F database failure | dead store → **durable audit spool** → recovery → `replay_spooled()` → verified |
| G provider failure | failing provider → **`provider_failure` metric** → deterministic fallback → audit |

## 2. Multi-client consistency

Web (aura-web), desktop, and mobile clients all speak the canonical API/SDK
contracts (typed `AuraApi`, `/health /ready /v1/reason`); business rules live in
the canonical runtime (`aura/`), not in clients (see `docs/TESTING.md`,
`docs/PROVIDERS.md`). Desktop/mobile reuse the SAME `aura.clients` primitives
(secure storage + offline queue) rather than duplicating logic.

## 3. Data consistency / fault injection

Covered by the failure-path suites + scenarios F/G: concurrent writes
(`test_distributed.py`), retries/idempotency (audit `event_id`, offline queue
LWW), duplicate requests, partial failure (PG backup no-clobber), rollback
(`pg_backup` force-restore), recovery/replay (spool resync).

## 4. Performance acceptance (local baseline)

`scripts/benchmark_phase35.py` (single machine, in-process):

| path | ms/call | ops/s |
|------|---------|-------|
| reason (deterministic) | ~0.170 | ~5,900 |
| reason + synthesis provider | ~0.179 | ~5,600 |
| memory write | ~0.005 | ~188,000 |

Classified LOCAL BASELINE ONLY — no staging/load soak was run (requires
infrastructure; recorded in `docs/PERFORMANCE.md`).

## 5. Release security (as of this gate)

- `pip-audit` clean (after pip 26.2.1 upgrade) · `npm audit --omit=dev` 0 ·
  secret scan clean (21 hits classified, none real) ·
  `security_check.py` AST-based clean · CycloneDX SBOM generated (78 components).

## 6. Repository hygiene

- Removed the two untracked 15/12-byte migration-stray `query` files
  (`E:\AURA\query`, `06_SOURCE_CODE/aura/query`).
- `E:\AURA\.agents` scratch/throwaway-PG data fully removed.
- `06_SOURCE_CODE/pgtest_data/` and the migration artifacts remain untracked
  (historical migration state; left for operator decision, not deleted).

## 7. Known limitations / classifications

- Live provider calls, live cloud deployment, desktop/mobile packaged
  launches, and browser-automated web E2E: **NOT VERIFIED / ENVIRONMENT
  DEPENDENT** (no credentials/toolchains).
- Streaming API, alert delivery platform: **NOT SUPPORTED / operator-wired**.
- Performance numbers are local-only.
- Compliance framework is readiness-only (no certification claims).