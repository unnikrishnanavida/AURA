# Phase 28 — Production Baseline Acceptance Report

**Status:** COMPLETE. Gate evidence below. Commit: `chore(phase28)`.
Full test suite **359/359** pass (exit 0) incl. live PostgreSQL 18
integration; mypy strict clean; ruff clean.

---

## 1. Clean install (§28.1) — PASS

Performed in a **temporary isolated environment** (gitignored `build/.phase28`):
fresh `venv`, wheel built from canonical source (`python -m build --wheel`),
installed with real dependencies from PyPI (pydantic 2.13.5, PyYAML 6.0.3),
plus pip upgraded to 26.2.1. Verified with **scrubbed `AURA_*` environment**
and no dependency on the developer machine / stale cache / old C: path:

| Check | Result |
|---|---|
| `import aura` resolves to venv `site-packages` | PASS (not the source tree) |
| `aura version` / `aura doctor` | 0.2.0; runtime imports ok, dev tools correctly absent in clean install |
| `aura config validate` (production+sqlite via env) | `environment=production` (after P28-2 fix) |
| `aura run "what is 2+2?"` | real reasoning pass (honest "I do not know" @ 0.0 on no evidence) |
| API /health, /ready | 200 / 200 |
| Auth missing / wrong / right | 401 / 401 / 200 |
| Bad body (input validation) | 400 |
| /v1/remember + /v1/reason + /v1/recall | 200 / 200 / 200 |
| Shutdown + **restart** (new process, same SQLite) | recall across restart `n=1` |
| Installed-package grep for `C:\Users\navid` | 0 |

## 2. Canonical path audit (§28.2) — PASS

All **16,909 tracked files** scanned for `C:\Users\navid` (any case/separator):
**0 references.** No stale runtime/config references at HEAD. The deleted path
appears only in untracked migration documentation (intentional history).

## 3. Production topology (§28.3)

- **TLS edge** — `tests/api/test_tls_proxy.py` (real ephemeral CA + HTTPS
  proxy): PASS.
- **Two instances + PostgreSQL** — `test_multi_instance.py` +
  `test_distributed.py` against a real throwaway PostgreSQL 18 cluster: PASS
  (shared sessions, key-revocation propagation, shared atomic rate limiting,
  durable session restart).
- **Live HTTP dual-instance** — two real API servers on different ports,
  one PostgreSQL: `/health` shows `PostgreSQLMemoryStore` on both; A-session
  readable on B; A-written memory recalled on B (`n=1`).
- **Docker compose** — both compose files YAML-valid and content reviewed.
  **ENVIRONMENT DEPENDENT:** Docker daemon not running; no container bring-up
  executed locally (no fake claim).

## 4. Security baseline (§28.4) — PASS

- Suites `tests/security`, `test_tls_proxy.py`, `test_api_security.py`,
  `test_prompt_injection.py`, `test_defense_pipeline.py`, `tests/core`,
  `tests/config`: all PASS.
- Black-box HTTP checks: 401 missing/wrong key, 400 malformed body, session &
  rate-limit behavior, fail-closed distributed policy, secret redaction,
  audit with stable `event_id` (Phase 27), security headers.

## 5. Release security (§28.5)

| Tool | Result |
|---|---|
| `pip-audit` (before) | **10 known vulnerabilities in pip 25.3** (PYSEC-2026-1796/196/2875/2876/3721) |
| fix | pip upgraded to **26.2.1**; re-audit **No known vulnerabilities found** |
| `npm audit --omit=dev` | **0 vulnerabilities** |
| repo secret scan (16,909 files) | 21 hits **all classified** (`.env.example` placeholders, "token"-module false positives, an enum literal `PASSWORD = "password"`, one documented dev-only compose placeholder) — **no real credentials** |
| `scripts/security_check.py` | AST-based `eval`/`exec` detection; **clean** |
| SBOM | CycloneDX 1.4 (`pip-audit -f cyclonedx-json`): **78 components**, audit clean |

## 6. Backup / restore (§28.6) — REAL DRILL PASS

- **PostgreSQL**: seed 2 → `create_pg_backup` (logical export, schema_version=1
  manifest, integrity check) → TRUNCATE (simulated loss; count 0) →
  `restore_pg_backup` → count 2 with original keys → **no-clobber gate**
  (`force=False`) correctly refuses restore onto non-empty target.
- **SQLite**: seed → file-copy backup → delete all → restore → count restored.
- **Finding fixed (P28-5):** `create_pg_backup` crashed
  (`FileNotFoundError`) when `backup_dir` did not exist; it now creates it.
  Regression test `test_pg_backup_creates_missing_backup_dir` added.

## 7. Findings fixed in Phase 28

| ID | Finding | Fix | Regression test |
|----|---------|-----|-----------------|
| P28-1 | SQLite connection not closed on shutdown → transient `database is locked` on immediate restart (Windows WAL) | `AuraApiServer.close()` closes the store; wired into `run_server()` | `test_server_close_*` (2 tests) |
| P28-2 | `load_settings()` (CLI path) ignored `AURA_*` env → `config validate` showed development under production env | layered defaults < file < env < explicit args | `test_load_settings_honors_environment_variables` (+2) |
| P28-3 | distributed-state pool not closed → `ConnectionPool.__del__` noise at exit | `close()` also closes `_distributed_state` | `test_server_close_closes_distributed_state_pool` |
| P28-5 | `create_pg_backup` required existing backup dir | `mkdir(parents=True)` before export | `test_pg_backup_creates_missing_backup_dir` |
| — | `security_check.py` false-positived `"eval("`/`"exec("` literals | AST-based detection | manual probe: real call flagged, literal ignored |
## 8. Phase 28 gate

| Gate | Evidence |
|------|----------|
| [x] clean installation | wheel install into fresh venv + full CLI/API smoke |
| [x] clean startup | `/health` `/ready` 200; config validated |
| [x] clean shutdown | `close()` releases store + pool; no lock race on restart |
| [x] restart | new process read persisted SQLite data |
| [x] database migration | fresh PG/sqlite migrations applied; schema_version=1 |
| [x] authentication | 401/401/200 black-box; key issuance/revocation tests |
| [x] authorization | admin-gated key endpoints; capability tests |
| [x] TLS baseline | `test_tls_proxy.py` (real CA), security headers |
| [x] security baseline | security/core/config suites PASS |
| [x] backup | PG logical + SQLite file-copy, integrity-checked |
| [x] restore | PG round-trip + no-clobber; SQLite round-trip |
| [x] full tests | **359/359** (exit 0) with live PostgreSQL |
| [x] static analysis | ruff clean; mypy strict clean |
| [x] dependency/security analysis | pip-audit clean, npm audit 0, secret scan clean, SBOM generated |
| [x] canonical path audit | 0 references across 16,909 tracked files |

## 9. Known limitations / classifications

- Docker compose bring-up: **ENVIRONMENT DEPENDENT** (no Docker daemon).
- Real-PG integration tests are DSN-gated and were executed against a
  throwaway cluster that has been stopped and removed.
- `npm audit`: production path audited (`--omit=dev`); full-tree scope is
  documented in `docs/SECURITY_OPERATIONS.md`.
- Install-time tool pin: `pip>=26.2.1` recommended for base images (fixes the
  PYSEC advisories found by `pip-audit`).

## 10. Untracked leftovers (not canonical)

`query` (repo root) and `06_SOURCE_CODE/aura/query` are 15/12-byte untracked
files containing `postgresqlx64` / `postgresql` (stray migration output). They
are untracked, not part of the runtime, and were not modified; removal is
deferred to the final repository-hygiene pass.