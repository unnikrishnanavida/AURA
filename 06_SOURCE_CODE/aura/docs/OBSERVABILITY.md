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
