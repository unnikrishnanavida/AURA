# Phase 27 — Durable Audit + Production Reliability Report

**Status:** COMPLETE. Acceptance gate passed: full suite **356/356** (exit 0)
against a real PostgreSQL 18 cluster, mypy strict clean, ruff clean, API smoke
verified.

---

## 1. Previous state (inspection result)

`aura.security.audit.AuditLog` was an in-memory append log with an optional
sink. `aura.api.distributed.PostgreSQLAuditLog` provided a durable
`aura_audit_events` table with a bounded (<=1000) in-memory fallback. The
flight recorder already established the durable pattern to reuse: `EventId`,
`PostgreSQLFlightRecorder` (`ON CONFLICT ... DO NOTHING`), and `ReplayEngine`.

Gaps found:

| # | Gap | Consequence |
|---|-----|-------------|
| 1 | No stable event identity on audit records | cross-instance dedup / resync impossible |
| 2 | Volatile fallback (in-memory only) | outage records lost at process exit |
| 3 | No idempotent writes | replay/resync could duplicate |
| 4 | No replay / filtered query surface | `entries()` returned the whole table only |
| 5 | No test coverage for `PostgreSQLAuditLog` | regressions invisible |

## 2. What was built

- **`aura/security/audit.py`** — `AuditRecord` now carries a stable `event_id`
  (`EventId`); `record()` accepts `event_id=`, an explicit `payload=` mapping,
  and flat extra keyword payloads (merged; see §3). Backward compatible.
- **`aura/security/spool.py`** (new) — `AuditSpool`: append-only local JSON-lines
  durability with atomic rewrite on `remove()`; torn crash lines are skipped
  without blocking replay.
- **`aura/api/distributed.py`** — `PostgreSQLAuditLog`:
  - schema ensure/upgrade (advisory-locked): `event_id` column + deterministic
    backfill + unique index (`ux_aura_audit_event_id`);
  - idempotent `INSERT ... ON CONFLICT (event_id) DO NOTHING`;
  - outage fallback: bounded buffer **+ durable spool**;
  - `replay_spooled()` — idempotent resync (`... DO NOTHING RETURNING
    event_id`), spool cleared only after full success, left intact when the
    store is still down;
  - `entries(event_id=, actor=, decision=, action=, correlation_id=, since=,
    limit=)` parameterized filters; local buffer+spool served (deduplicated by
    `event_id`) when the store is unreachable; `count()`.

## 3. Latent bug found and fixed

`record(..., **payload)` plus a keyword literally named `payload={...}` (as the
existing `PostgreSQLApiKeyStore.issue` already used) bound
`{"payload": {...}}` — the parameter name collided with the caller's keyword
name and payloads were silently double-nested. Fixed by an explicit `payload`
parameter merged with extra keyword payloads. Caught live by the real-PG
integration gate (the payload assertion failed); unit tests with simulated
store connections had not covered a literal `payload=` call.

## 4. Tests

- `tests/security/test_audit_spool.py` — 5 unit tests: append/read order,
  restart durability, atomic remove, clear, torn-line tolerance.
- `tests/security/test_audit_durable.py` — 11 failure-path unit tests with a
  simulated store: idempotent SQL + event_id on insert, auto event_id,
  spool+buffer on outage, resync-and-clear, spool-kept-while-down,
  skip-already-present, parameterized WHERE + LIMIT, row mapping, local-truth
  fallback, count with local fallback, `coerce_event_id`.
- `tests/api/test_distributed.py` — 5 new DSN-gated real-PostgreSQL integration
  tests: durable lifecycle + idempotent duplicate, cross-instance visibility,
  filters (actor/decision/since/event_id), spool replay/resync, skip-existing.
  Each is scoped to unique actors/events because the module shares one real
  test database.

## 5. Verification evidence (2026-09-25)

- Full suite with real PostgreSQL (throwaway PostgreSQL 18 cluster, trust auth):
  **356 collected, 356 pass, exit 0** (includes memory/PG, backup, distributed,
  and API multi-instance tests).
- `mypy` strict: clean on `audit.py`, `spool.py`, `distributed.py`.
- `ruff` (E/F/I/UP/B/SIM): clean on all changed src + test files.
- API smoke: `GET /v1/audit` -> 200 with `"event_id": "ev-..."` and flat
  `"payload": {"k": 1}`.
- Throwaway cluster data directory and log were removed after the gate; no
  Docker or C: drive state was touched.

## 6. Known limitations / not verified

- Real-PG integration tests are DSN-gated (`AURA_TEST_POSTGRESQL_DSN`) and
  require the operator's PostgreSQL instance; they were executed here against a
  throwaway local cluster and will skip when no DSN is configured.
- The spool is a single append-only file per process spool directory; very
  large outage windows are bounded only by the spool clearing on resync.
- `timestamp >= since` filtering compares ISO-8601 text; producers must use the
  same clock format (the codebase's `SystemClock` always does).
- Alert delivery and cross-region rate limits remain as documented in
  `docs/OBSERVABILITY.md` / `docs/SECURITY_OPERATIONS.md` (unchanged by this
  phase).

## 7. Next steps

Phase 28 (see root roadmap once populated; otherwise prior phases' conventions):
candidate areas from this phase's surroundings — durable flight-recorder spool
mirroring the audit spool, alert-rule delivery wiring, or deployment
hardening. No Phase 28 work has been started.