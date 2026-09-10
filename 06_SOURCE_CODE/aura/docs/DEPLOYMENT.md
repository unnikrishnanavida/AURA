# AURA Deployment Architecture (Phases 11, 13-16)

## Environments

| Env        | Config file                   | Storage    | Enforced gates                                             |
| ---------- | ----------------------------- | ---------- | ---------------------------------------------------------- |
| LOCAL/DEV  | `config/env/development.yaml` | memory     | none (safe dev defaults)                                   |
| TESTING    | `config/env/development.yaml` | memory     | tests always inject stores explicitly                      |
| STAGING    | `config/env/staging.yaml`     | sqlite     | persistent backend required                                |
| PRODUCTION | `config/env/production.yaml`  | postgresql | persistent backend + issuer secret >= 16 chars; DSN required |

Production configuration is validated by
`scripts/validate_deployment.py` and enforced by `aura.api.server.run_server`
- the server **refuses to start** with an in-memory backend, a missing/weak
`AURA_API_SECRET`, or a postgresql backend without `AURA_STORAGE_POSTGRESQL_DSN`,
and never silently downgrades a secure production config.

## Persistence backends

- `memory` - development only; lost on restart.
- `sqlite` - file-backed WAL store with migrations, transactions, integrity
  checks (default persistent choice for single-instance/small deployments).
- `postgresql` - durable shared store using `psycopg3` + `psycopg-pool`
  (optional dependency: `pip install aura[postgresql]`). Versioned migrations
  in `aura.memory.pg_migrations` run transactionally at startup; incompatible
  schemas refuse startup. All three backends share the same `MemoryStore`
  contract and identical `MemoryEntry` semantics.

## Distributed state (multi-instance)

When `AURA_API_DISTRIBUTED_STATE_DSN` is set, API instances share one
PostgreSQL database for:

- **sessions** - durable, expiring, revoked-session reject; survive restarts.
- **API keys** - shared HMAC-digest lifecycle; revocation propagates instantly
  across instances.
- **rate limiting** - atomic token bucket (single SQL statement), shared across
  instances; bounded cleanup.
- **audit** - append-only `aura_audit_events`, visible from every instance.
- **flight recorder** - shared execution trajectory so replay works from any
  instance.

**Failure policy is explicit.** If the distributed store is unreachable:
`fail_closed` (default) denies requests; `bounded_local` throttles per instance.
It never silently fails open. The audit log buffers locally and never breaks the
request path.

## Multi-instance topology + TLS

```
                INTERNET
                    |
                    v
          REVERSE PROXY / TLS  (TLSProxy: TLS termination, HTTP->HTTPS
                    |          redirect, round-robin + upstream failover)
          --------------------
          |                  |
          v                  v
      AURA API A         AURA API B      (shared PostgreSQL state + memory)
          |                  |
          -----------+--------
                    |
              PostgreSQL
```

- The reverse proxy terminates HTTPS and forwards to the API instances; the API
  honors `X-Forwarded-For` only when `trust_proxy=true` (spoofing blocked).
- A dead upstream fails over to the next healthy instance; if none are healthy
  the request fails 502.
- Test certificates for local/staging validation are generated ephemerally by
  `aura.api.tls_testing` - **never committed**. Production cert/key come from
  the operator and are documented in `PRODUCTION_CANDIDATE_REPORT.md`.
- Local topology: `compose.postgres.yaml` (postgres + two API instances, no
  proxy); full proxy+TLS drill: `evaluation/production_topology_e2e.py`.

## Health/readiness/liveness

- `/liveness` - process alive; no dependency touch (used by container healthcheck).
- `/health` - engine status **plus** a real dependency round-trip
  (`store.count()` against the configured backend). Returns 503 when the
  dependency is down instead of a false "healthy".
- `/ready` - health + dependency; returns 200 only when work can be accepted.
- Security headers are set on every response regardless of the TLS terminator:
  `X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY`,
  `Referrer-Policy: no-referrer`, `X-Request-Id`.

## Backup / recovery

- **SQLite**: canonical `create_backup`/`restore_backup` (online copy +
  integrity check + schema-compatibility gate). CLI:
  `python -m aura.observability.backup_cli`.
- **PostgreSQL**: `aura.observability.pg_backup` - deterministic logical export
  (psycopg-only, no `pg_dump` requirement) with manifest + schema-version
  check; restore refuses to clobber a populated database unless `force=True`
  and only touches AURA tables. Operators may additionally use `pg_dump` for
  full-database backups.
- Retention/frequency are operator-controlled (atomic timestamped snapshots;
  keep N most recent).

## Containerization

- `Dockerfile` - non-root runtime (`aura` user), Python slim base, installs
  the core dependencies plus the optional `postgresql` extra when the
  deployment requires it. Bind-mounted `/data` volume for SQLite; PostgreSQL
  connections come from the DSN (never baked into images).
- `compose.yaml` - single API instance + SQLite volume (local dev).
- `compose.postgres.yaml` - PostgreSQL + two API instances sharing one database
  (multi-instance local validation). No proxy; run
  `evaluation/production_topology_e2e.py` for the full TLS-proxy topology.
- Health checks use `/liveness`; readiness is `/ready` (checks the actual
  persistence dependency).

## Operations

- Validate a deployment before start: `python scripts/validate_deployment.py <env>`.
- Verify the whole ecosystem (release gate, incl. optional live-PostgreSQL
  gates when `AURA_TEST_POSTGRESQL_DSN` is set):
  `python 06_SOURCE_CODE/scripts/verify_ecosystem.py`.
- Run the production topology drill: `python 06_SOURCE_CODE/evaluation/production_topology_e2e.py`.
- Backup: `python -m aura.observability.backup_cli` (SQLite) or
  `aura.observability.pg_backup.create_pg_backup` (PostgreSQL).

## Security notes

- TLS terminates at the proxy; the API does not serve TLS directly.
- Reverse-proxy trust: only the proxy may set `X-Forwarded-For`; direct clients
  cannot spoof their rate-limit bucket.
- Restricted endpoints are auth + admin-key gated; API keys are HMAC-digested;
  sessions/keys/limits/audit are shared for multi-instance consistency.
- Secrets (API secret, PostgreSQL passwords, proxy keys) live in environment /
  secret stores; never in source control (see `.env.example`).