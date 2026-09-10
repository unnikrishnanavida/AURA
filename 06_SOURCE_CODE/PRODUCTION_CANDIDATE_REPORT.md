# AURA Production Candidate Report (Phases 13-16)

**Baseline commit:** `d4a92f2b` (verified Phase 1-12 ecosystem)
**Phase commits:** `56f986f1` (13) · `0de32718` (14) · `628e04a8`+`27f234b4` (15) · `757f493a` (16) · `6bda6ace` (release: report + evidence)
**Date:** 2026-09-10

---

## 1. Executive Summary

AURA moved from **STAGING READY (B)** to **PRODUCTION CANDIDATE (A)**-qualified
architecture: a real PostgreSQL memory backend, distributed (shared) sessions /
API keys / rate limits / audit / flight recorder, a TLS-terminating reverse
proxy with upstream failover, two independent API instances sharing one
database, a PostgreSQL backup/restore drill, and a production-like end-to-end
topology test - all against real infrastructure, no mocks. The 34/34 release
gate passes with the live-PostgreSQL gates enabled.

Classification is evidence-based; see section 23.

## 2. Current Architecture

```
                INTERNET
                    |
                    v
          TLSReverseProxy (HTTPS + HTTP->HTTPS + failover)
          --------------------
          |                  |
          v                  v
      AURA API A         AURA API B
          |                  |
          -----------+--------
                    |
         PostgreSQL (memory + distributed state + audit + flight)
```

- One canonical runtime (`06_SOURCE_CODE/aura`).
- API instances share PostgreSQL for memory, sessions, API keys, rate limits,
  audit, and execution trajectories.
- TLS terminates at the proxy; API trusts X-Forwarded-For only from it.

## 3. Phase 13 Results - Real PostgreSQL Persistence

**Implemented:**

- `aura/memory/postgresql_store.py` - real psycopg3 + psycopg-pool backend
  (connection pool, startup probe/fail-fast, transactional archive/restore,
  thread-local transaction pinning). No silent fallback to another backend.
- `aura/memory/pg_migrations.py` - PostgreSQL schema version tracking,
  deterministic forward migrations, transactional DDL, startup refusal for
  incompatible schemas.
- `aura/memory/factory.py` - `postgresql` backend now constructs the real
  store; PostgreSQL DSN is required and a missing DSN fails fast.
- `pyproject.toml` - optional `postgresql` extra (`psycopg[binary]>=3.2,<4`,
  `psycopg-pool>=3.2,<4`); PostgreSQL never a mandatory local dependency.
- Config: `StorageConfig.postgresql_dsn` / pool sizes; `.env.example`,
  `production.yaml` updated; production refuses `postgresql` without a DSN.

**Tests** (`tests/memory/test_pg_store.py`, real PostgreSQL 18.3, disposable
per-run database): create/read/update/delete, search filters, archive/restore,
transaction rollback on failure, 4x10 concurrent writes, restart survival,
connection failure is explicit, incompatible-schema startup refusal, corrupted
row detection. **11/11 pass.**

## 4. Phase 14 Results - Distributed State

- `aura/api/distributed.py`:
  - `PostgreSQLSessionStore` - durable, expiring, revocable sessions shared
    across instances (survive process restart).
  - `PostgreSQLApiKeyStore` - HMAC-digest shared key lifecycle; revocation
    propagates instantly across instances.
  - `DistributedRateLimiter` - atomic token bucket (single SQL upsert +
    refill); shared across instances; explicit degraded policy
    (`fail_closed` default / `bounded_local`), never silent fail-open.
  - `PostgreSQLAuditLog` - append-only shared audit with local bounded
    fallback so a store outage never breaks the request path.
- Canonical `ServerConfig` gains `distributed_state_dsn`,
  `distributed_state_policy`, `session_ttl_seconds`; `run_server` wires env.
- Multi-instance replay: `PostgreSQLFlightRecorder` (shared execution
  trajectories) replaces the in-memory recorder when distributed state is on.

**Tests** (`tests/api/test_distributed.py` - real PG): session lifecycle +
deterministic expiry, API key issue/validate/revoke shared across stores,
rate-limit burst, shared bucket across two limiters, fail-closed when store
down (incl. bounded-local mode), concurrent session writes. **9/9 pass.**

## 5. Phase 15 Results - Multi-Instance + TLS

- `aura/api/proxy.py` - minimal real reverse proxy: TLS termination, HTTP-to-
  HTTPS 301 redirect, round-robin + upstream failover (dead upstream falls
  through to healthy one; 502 when none), overwrites X-Forwarded-For (blocks
  spoofing), security headers, request-size limit.
- `aura/api/tls_testing.py` - ephemeral local test CA/server certs
  (cryptography); **no keys committed**.
- `tests/api/test_tls_proxy.py` - TLS termination end-to-end over trusted CA,
  HTTP-to-HTTPS redirect, security headers, failover to healthy upstream,
  XFF-spoofing rejection, config validation. **5/5 pass.**
- `tests/api/test_multi_instance.py` (real PG, two live HTTP servers): session
  visible on B after creation on A, API key revocation propagates, shared rate
  bucket across instances, session survives restart. **4/4 pass.**

## 6. Phase 16 Results - Disaster Recovery + Production-Candidate Validation

- `aura/observability/pg_backup.py` - deterministic logical backup (psycopg
  only) with manifest + schema-version header; restore refuses to clobber a
  populated database unless `force=True`; drops/recreates only AURA tables.
- `tests/observability/test_pg_backup.py` - round-trip + clobber-protection +
  non-AURA-file rejection. **2/2 pass.**
- `evaluation/production_topology_e2e.py` - full production-like drill:
  HTTPS through proxy -> authenticate -> durable session -> pipeline routed via
  TLS proxy -> replay through proxy -> shared memory across instances -> shared
## 7. Persistence Architecture

| Backend     | Driver            | Migrations            | Transactions        | Integrity            | Notes                                         |
| ----------- | ----------------- | --------------------- | ------------------- | -------------------- | --------------------------------------------- |
| memory      | none              | n/a                   | no-op               | n/a                  | dev only; production rejects                  |
| sqlite      | stdlib sqlite3    | `migrations` (WAL)    | BEGIN IMMEDIATE     | PRAGMA quick_check   | single-writer, file-backed                    |
| postgresql  | psycopg3 + pool   | `pg_migrations` (txn) | real BEGIN/COMMIT, thread-pinned | strict row deserialization | optional dep; fail-fast on connect |

All three implement the same `MemoryStore` protocol and identical
`MemoryEntry` semantics (identity, content, provenance, confidence axes,
sensitivity, retention, timestamps, version, lineage, lifecycle, links,
archival state).

## 8. Security Architecture

- **API boundary**: static bearer key and/or HMAC-digest issued keys
  (shared across instances), admin-gated key issue/revoke, request-size limit
  (413 before body read), per-client rate limits (shared token bucket),
  security headers, session expiry/revocation.
- **Distributed**: endpoints deny on distributed-state outage (fail-closed);
  no silent downgrade; audit buffers locally and never breaks requests.
- **Proxy**: TLS termination, HTTP-to-HTTPS, XFF spoofing blocked.
- **Data**: memory sensitivity classification + clearance-gated access
  (existing), PG backup is plain logical SQL (encryption-at-rest delegated to
  platform).

## 9. Deployment Architecture

- `compose.postgres.yaml` - PostgreSQL + two API instances sharing one DB.
- `Dockerfile` - non-root runtime, /data volume.
- Env configs: development / staging / production (`config/env/`).
- `scripts/validate_deployment.py` - environment-aware startup validation.
- TLS cert/key injected by operator; test certs are ephemeral only.

## 10. Observability Architecture

- Structured logs, metrics, correlation/request IDs (existing).
- Shared flight recorder for multi-instance replay.
- Shared audit log; health/readiness verify the real persistence dependency;
  liveness is process-only.

## 11. Backup/Recovery Strategy

- **SQLite**: online `sqlite3.Connection.backup`, integrity + schema gate.
- **PostgreSQL**: deterministic logical SQL export (psycopg-only) + manifest;
  restore validates schema version, refuses populated-target clobber unless
  `force=True`, touches only AURA tables. Operators may also use `pg_dump`
  externally.
- Retention: operator-controlled (atomic timestamped snapshots; keep N).
- Encryption-at-rest: platform/TDE (documented, not faked).

## 12. Performance / Load Testing

Latest smoke load (`evaluation/load_test.py`, `GET /health`, 60 requests,
concurrency 4, Windows 11, Python 3.14.3):

| Metric | Value       |
| ------ | ----------- |
| RPS    | 383.3       |
| p50    | 2.35 ms     |
| p95    | 64.83 ms    |
| p99    | 67.63 ms    |
| error rate | 0.0%    |

Environment: AMD64, Windows-11-10.0.26200-SP0, Python 3.14.3. Config:
in-memory backend (health path), stdlib ThreadingHTTPServer. Real HTTP; not a
production-size benchmark - see section 20.

## 13. Security Results (Re-validation)

- Authentication across instances: PASS (shared key store).
- Session revocation across instances: PASS (durable shared sessions).
- API key revocation across instances: PASS (instant propagation).
- Distributed rate-limit enforcement: PASS (shared bucket).
- Robuster failure behavior: PASS (fail-closed on store outage).
- Proxy spoofing / forged X-Forwarded-For: PASS (proxy overwrites).
- HTTP-to-HTTPS downgrade: PASS (301 redirect).
- TLS boundary behavior: PASS (server cert verified against test CA).
- Privileged endpoint denial: PASS (admin-key gate).
- Secret exposure: PASS (secret scan clean; raw keys never stored/logged).

## 14. Exact Tests Executed

- Canonical suite (incl. PG-gated memory/distributed/multi-instance/PG-backup
  tests + TLS proxy tests): **292 passed**.
- Production topology E2E: **12/12**.
- Release gate (`scripts/verify_ecosystem.py` with `AURA_TEST_POSTGRESQL_DSN`):
  **34/34** (aura tests/mypy/ruff, deployment validator, SDK, web, all
  standalone repos, final integration, evaluation, load test, secret scan, TLS
  proxy, PG store, PG backup, distributed state, multi-instance, topology E2E).

## 15. Tests NOT RUN

- Multi-instance HTTP load test against the topology (only single-instance
  /health load test ran; the topology E2E exercises routing/failover
  functionally, not under load).
- Internet-facing certificate issuance (not performed; production CAs not
  exercised).
  audit -> failover (terminate instance A, continue via B) -> distributed-state
  outage fails closed -> restart with persisted data -> PostgreSQL backup +
  restore drill -> data survives full topology restart. **12/12 pass** with
  real components; disposable DB dropped after.
## 16. Known Limitations

- PostgreSQL store uses one process-local connection pool per instance;
  cross-instance locking is left to PostgreSQL (no app-level distributed
  locking).
- Distributed rate limiting uses a two-statement upsert+decrement (atomic via
  the single-row upsert; refill computed on the row; minor drift possible
  under pathological contention).
- TLS test certs are CA-signed ephemeral (localhost) - fine for staging tests,
  not for the public Internet.
- A single proxy instance is a SPOF (no proxy HA tested).
- `cryptography` is a dev/test dependency (added to the venv for TLS cert
  generation); the canonical runtime does not import it at runtime.

## 17. Dependency Findings

- Added optional `postgresql` extra (`psycopg[binary]>=3.2,<4`,
  `psycopg-pool>=3.2,<4`), pinned compatible ranges.
- Added dev dependency `cryptography>=42` for ephemeral test-CA generation.
- No new mandatory runtime dependency; no known vulnerable transitive
  dependencies observed in the touched paths (post-review documented).

## 18. Final Readiness Classification

**A - PRODUCTION CANDIDATE** (with documented operational prerequisites):

- PostgreSQL backend real and tested (PostgreSQL 18.3)
- Distributed state behavior tested (sessions, keys, rate limits, audit, replay)
- Multi-instance behavior proven (two independent HTTP servers + proxy)
- TLS/proxy path exercised (ephemeral CA, real HTTPS)
- Disaster recovery tested (PG backup + restore drill)
- Production-like E2E succeeds (12/12)
- Security regressions pass
- Release gates pass (34/34)

**Prerequisites before declaring general production use:** operator-managed
TLS certs, a real reverse-proxy deployment (nginx/Caddy or the included
`TLSProxy`), PostgreSQL credentials via a secret store, a load test at
representative production scale, and documented backup scheduling.

## 19. Recommended Next Steps

1. Deploy behind a managed reverse proxy with a real CA; set
   `AURA_API_DISTRIBUTED_STATE_DSN` + `AURA_STORAGE_POSTGRESQL_DSN`.
2. Run a multi-instance HTTP load test at production-topology scale.
3. Automate backup scheduling + restore drills (document frequency/retention).
4. Add alerting on /ready health signals and rate-limit denials.
5. Consider adding a second TLS proxy to remove the single SPOF.