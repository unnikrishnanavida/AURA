# AURA Deployment Runbook

Operational runbook for deploying and running the AURA API in local, staging,
and production-like topologies. Everything here is reproducible from the
repository.

## Prerequisites

- Python >= 3.11 for source installs; or a Docker daemon for containers.
- PostgreSQL 16+ for the production / multi-instance backend (or SQLite for
  single-node).
- `AURA_TEST_POSTGRESQL_DSN` pointing at a reachable PostgreSQL to exercise
  PG-gated verification.

## Configuration

All configuration is environment-variable driven (production refuses unsafe
defaults). Key variables:

- `AURA_ENVIRONMENT` — `development | testing | research | staging | production`
- `AURA_STORAGE_BACKEND` — `memory | sqlite | postgresql`
- `AURA_STORAGE_POSTGRESQL_DSN` — required for `postgresql`
- `AURA_API_DISTRIBUTED_STATE_DSN` — shared PG DSN for multi-instance
- `AURA_API_DISTRIBUTED_STATE_POLICY` — `fail_closed` (default) | `bounded_local`
- `AURA_API_KEY` / `AURA_API_SECRET` / `AURA_API_ADMIN_KEY`
- `AURA_API_TRUST_PROXY` — set `true` only behind the TLS proxy
- `AURA_API_ALLOW_PIPELINE` — `true` to enable the pipeline endpoint
- `AURA_API_RATE_BURST` / `AURA_API_RATE_PER_SECOND`
- `AURA_API_MAX_REQUEST_BYTES`, `AURA_API_SESSION_TTL_SECONDS`

Production gates enforced in `run_server`:
- refuses `backend=memory`
- refuses `backend=postgresql` without a DSN
- requires `AURA_API_SECRET` >= 16 chars

## Local single-node (source)

```bash
python -m venv .venv
.venv/Scripts/pip install '.[postgresql]'   # or without the extra for sqlite
AURA_STORAGE_BACKEND=sqlite \
AURA_STORAGE_SQLITE_PATH=data/aura.sqlite3 \
.venv/Scripts/python -m aura.api.server 0.0.0.0
```

## Container single-node (SQLite)

```bash
cd 06_SOURCE_CODE/aura
docker compose up -d --build          # compose.yaml (SQLite volume)
curl -fsS http://127.0.0.1:8765/ready
```

## Container multi-instance (PostgreSQL)

```bash
cd 06_SOURCE_CODE/aura
docker compose -f compose.postgres.yaml up -d --build   # postgres + 2 API instances
```

Both API instances share one PostgreSQL database (memory + distributed state:
sessions, keys, rate limits, audit, flight events). Health checks confirm the
backend is `PostgreSQLMemoryStore`.

## TLS reverse proxy topology

The production topology is internet -> TLS proxy -> two (or more) API
instances -> shared PostgreSQL. The included `TLSProxy` (or any managed proxy)
terminates TLS and sets `X-Forwarded-For`; API instances must run with
`AURA_API_TRUST_PROXY=true` and must not be directly reachable from untrusted
networks.

Full automated drill:

```bash
python 06_SOURCE_CODE/evaluation/production_topology_e2e.py
```

## Health & readiness

- `GET /liveness` — process alive.
- `GET /health` — engine health + real dependency round-trip (`store.count()`).
- `GET /ready` — accepts work only when the dependency is healthy.

## Validation commands

```bash
# Ecosystem release gate (40 gates; requires PG + optional Docker)
AURA_TEST_POSTGRESQL_DSN=... python 06_SOURCE_CODE/scripts/verify_ecosystem.py

# Clean install proof
python 06_SOURCE_CODE/evaluation/clean_install_test.py --with-tests

# Container lifecycle proof
python 06_SOURCE_CODE/evaluation/container_verify.py
```

## Phase 28 production-baseline verification (2026-09-25)

Behavior verified in the Phase 28 acceptance gate that operators should rely on:

- **Clean install** — `python -m build --wheel` + `pip install` into a fresh
  isolated venv, then `aura doctor` / `aura config validate` / `aura run`,
  API startup on a throwaway port, health/readiness, authentication, normal
  operation, shutdown, restart with data retained. No dependency on developer
  machine state, stale cache, or the deleted `C:\Users\navid\Desktop\AURA`
  path (all 16,909 tracked files audited: **0 references**).
- **Environment parity** — the CLI configuration path (`load_settings`) honors
  the same `AURA_*` environment variables as the API server
  (`AURA_ENVIRONMENT`, `AURA_STORAGE_BACKEND`, `AURA_API_SECRET`), so a single
  environment file/injection drives both `aura config validate` and
  `run_server`.
- **Clean shutdown** — `AuraApiServer.close()` releases the memory store
  connection and the distributed-state connection pool deterministically
  (SQLite WAL lock is released before process exit; PostgreSQL pool threads are
  joined). `run_server` invokes it in the shutdown path.
- **Backup/restore** — `create_pg_backup(dsn=..., backup_dir=...)` creates the
  backup directory itself (a fresh path no longer fails). Backup→restore
  round-trip, the no-clobber safety gate, and the SQLite file-copy drill are
  covered by regression tests and were executed against a real PostgreSQL 18
  instance during the gate.
- Backup: see `docs/BACKUP_AND_RECOVERY.md`.
- Rollback: see `docs/ROLLBACK_RUNBOOK.md`.
- Alerting: rules are specified in `docs/OBSERVABILITY.md`; wire your own
  delivery platform (none is built in).

## Local isolated staging (verified playbook, Phase 36)

A fully reproducible staging deployment of the canonical runtime over a real
PostgreSQL cluster, with zero production/system exposure. This is the exact
procedure exercised and PASSED in Phase 36 (see
`PHASE_36_STAGING_ACCEPTANCE_REPORT.md`).

```
# 1) throwaway PostgreSQL cluster (isolated, loopback only)
initdb -D <work>/pgstaging_data -U postgres -A trust -E UTF8 --no-locale
pg_ctl  -D <work>/pgstaging_data -o "-p 55499 -h 127.0.0.1" -l <work>/pgstaging.log start

# 2) deploy canonical application vs staging DB (fresh process)
python <aura>/build/staging_driver.py write     # migrates DB, seeds, runs staged round
# 3) restart = new process, same DB
python <aura>/build/staging_driver.py read      # proves persistence across restart
# 4) backup/restore drill + bounded HTTP load (thresholds defined pre-run)
python <aura>/build/stage36_h2.py
# 5) teardown
pg_ctl -D <work>/pgstaging_data stop -m fast
```

Notes:

- The staging driver is evidence tooling under `<aura>/build/` (gitignored);
  the application code deployed is the unmodified canonical runtime.
- Staging DBs are dedicated and empty at start; the app applies migration
  `version=1` itself.
- Rate-limiting and audit checks use throwaway tokens masked in output; all
  staging data lives in the throwaway cluster and is destroyed at teardown.
- Classify any attempt to reach live external providers or real cloud systems
  separately; the staged E2E in this playbook is provider-free and deterministic.