# AURA Observability + Alerting Specification

This documents the real signals AURA emits (metrics, structured logs, health
endpoints) and **specifes** alert rules. No alert delivery infrastructure is
implemented or claimed — rules are provided so operators can wire a platform
(PagerDuty, Opsgenie, Grafana Alertmanager).

## Application signals (from `aura.observability.metrics.Metrics`)

Counters: execution_count, execution_success, execution_failure, retries,
recovery_count, action_denials, tool_failures, provider_failures,
budget_consumption, memory_operations.
Gauges & latency histograms are exposed via `/v1/metrics` (authenticated) and
`/health` (engine + dependency).

Per-request structured logs carry `correlation_id`, `execution_id`, `ts`,
`level`, `logger`; secrets are redacted by `SecretRedactor` at the source.

## Database signals

- `/health` and `/ready` run a real `store.count()` round-trip; 503 when the
  dependency is down (not a false "healthy").
- `memory.persistence_error`-class failures surface in metrics counters and
  logs with the affected backend name.
- Migration failures raise `ConfigurationError` at startup (never silently
  proceed) and are log-visible.

## Security signals

- Authentication failures: `api.auth_failed` (4xx) + audit `decision=deny`.
- Authorization failures: `api.forbidden` + audit.
- Rate-limit denials: `api.rate_limited` + audit `rate_limit.deny`.
- Prompt-injection / policy denials: audit entries.

## Durable audit (Phase 27)

The security audit trail is durable, idempotent, and replayable:

- **Stable event identity** — every audit record carries an `event_id`
  (`aura.foundation.ids.EventId`); `GET /v1/audit` includes it.
- **Idempotent writes** — `PostgreSQLAuditLog` persists to `aura_audit_events`
  with `ON CONFLICT (event_id) DO NOTHING`, so retries, resync, and concurrent
  instances can never duplicate a record.
- **Outage behavior (fail-safe, never silent)** — when the shared store is
  unreachable a record is (a) kept in a bounded in-memory buffer for immediate
  in-process observability and (b) **durably spooled** to local JSON-lines
  files (`data/audit_spool/spool.jsonl` by default) so it survives restarts.
- **Replay / resync** — `PostgreSQLAuditLog.replay_spooled()` drains the spool
  into PostgreSQL once the store is reachable; already-present records are
  skipped (idempotent), and the spool is cleared only after a fully successful
  resync.
- **Query surface** — `entries(event_id=..., actor=..., decision=...,
  correlation_id=..., since=..., limit=...)` executes parameterized SQL;
  while the store is down the local buffer + spool are served (deduplicated by
  `event_id`, never fabricated).
- Schema upgrade is idempotent and concurrency-safe: the `event_id` column is
  added if missing, legacy rows are backfilled deterministically, and a unique
  index is created under an advisory lock (fresh DBs and pre-existing
  deployments are both handled).

## System signals

- `/liveness` (process alive), `/ready` (can accept work), `/health`
  (dependency health).
- Restart events: container/compose lifecycle; audit + metrics reset (metrics
  are in-memory per process).

## Pipeline signals

- Request lifecycle steps are recorded by the flight recorder
  (`aura_flight_events` in PG, or in-memory) and replayable via
  `/v1/replay/{id}` — memory→knowledge→research→reason→plan→security→exec→
  verify→reflect→learn→memory.
- Execution failure, retry exhaustion, cancellation, and recovery are recorded
  as events with origin/markers.

## Metric exposure

- `/v1/metrics` (authenticated) returns the in-process snapshot
  (`{"counters","gauges","latency"}`).
- Structured logs are JSON to stderr (container log collection).

## Alert rules (specification — not wired to a delivery platform)

| Signal | Condition | Severity | Rationale |
| ------ | --------- | -------- | --------- |
| Error rate | sustained >10% over 5 min (execution_failure/execution_count) | HIGH | degraded pipeline |
| Persistence | `/health` dependency ok=false for >2 consecutive probes | CRITICAL | DB unreachable |
| Auth attacks | >50 auth_failed from one IP in 5 min | HIGH | brute force |
| Rate limit denials | rate_limit.deny burst > threshold | MEDIUM | abuse / misconfig |
| Backup | backup job missing/exit != 0 in 24h | HIGH | no recovery path |
| Migration | startup ConfigurationError (schema mismatch) | CRITICAL | incompatible schema |
| Latency | p99 pipeline latency > threshold for 15 min | MEDIUM | capacity |

These are documented specifications only; configuring delivery is an operator
step and is not claimed to be live.
