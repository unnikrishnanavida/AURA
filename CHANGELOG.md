# Changelog

## [0.2.0] — 2026-Q3

### Phase 27 — Durable Audit + Production Reliability (2026-09-25)

- Audit records now carry a stable `event_id`
  (`aura.security.audit.AuditRecord`, backed by
  `aura.foundation.ids.EventId`); `GET /v1/audit` includes it.
- `PostgreSQLAuditLog` (`aura.api.distributed`) persists idempotently
  (`ON CONFLICT (event_id) DO NOTHING`) to `aura_audit_events`; the schema is
  upgraded in place (column add + deterministic backfill + unique index) under
  an advisory lock, so fresh and pre-existing deployments are both handled.
- Store-outage behavior is now durable: while PostgreSQL is unreachable a
  record stays observable in a bounded in-memory buffer **and** is spooled to
  local JSON-lines files (`aura.security.spool.AuditSpool`,
  `data/audit_spool/spool.jsonl`). `replay_spooled()` resyncs the spool
  idempotently after recovery and clears it only on full success.
- Audit query surface extended: `entries(...)` supports `event_id`, `actor`,
  `decision`, `action`, `correlation_id`, `since`, and `limit` filters, plus
  `count()`; local buffer + spool are served (deduplicated, never fabricated)
  during an outage.
- Fixed a latent `**payload` name-collision bug: `record(..., payload={...})`
  previously bound `{"payload": {...}}`; the API now accepts an explicit
  `payload` mapping (merged with flat extra keyword payloads).
- New tests: `tests/security/test_audit_spool.py` (5), 
  `tests/security/test_audit_durable.py` (11 failure-path unit tests),
  DSN-gated real-PostgreSQL integration tests in
  `tests/api/test_distributed.py`. Verified: full suite **356/356 pass**
  (exit 0) against a real PostgreSQL 18 cluster, mypy strict clean, ruff clean.
- Full detail: `06_SOURCE_CODE/aura/PHASE_27_DURABLE_AUDIT_REPORT.md`.

- Added the **integrated AURA platform** package at `06_SOURCE_CODE/aura`:
  foundation, config, core, memory, knowledge, reasoning, planning,
  reflection, learning, brain orchestration, security, observability,
  providers, SDK, API, CLI, Docker, compose, CI/CD, and 100+ tests.
- Consolidated the architecture baseline: earlier generated engine scaffolds
  are documented as historical source areas; the supported public surface is
  the integrated package.
- See `06_SOURCE_CODE/aura/CHANGELOG.md` for the per-package history.

## 0.1.0

- Initialized the AURA repository structure and scaffolded core documentation.
