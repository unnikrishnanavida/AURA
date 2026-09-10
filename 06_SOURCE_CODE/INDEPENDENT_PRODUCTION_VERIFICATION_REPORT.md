# AURA Independent Production Verification Report (Phases 17-24)

**Independent verification mission - evidence over prior claims.**
**Baseline commit:** `03ac48be` (pre-verification HEAD)
**Verification commits:** `dfad55fb`, `3dbaddea`, `eb3fae6a`, `4cafeba2`, `b2c3ba92`, `ad30bc41`
**Date:** 2026-09-10

---

## A. EXECUTIVE SUMMARY

The AURA ecosystem was independently verified against the repository itself
(not prior reports). Real infrastructure used: fresh Python virtualenvs, real
PostgreSQL 18.3 (disposable instance + Docker Compose postgres:16), a live
Docker daemon (Docker Desktop restarted during verification), real TLS
termination via ephemeral CA, a two-instance compose topology, and real HTTP.

Verified as working: clean install/build, container build + lifecycle
(pipeline -> persist -> restart), PostgreSQL persistence + migrations +
distributed state across two instances, TLS proxy behavior, backup/restore,
upgrade-path schema handling, dependency security (Python + npm), SBOM
generation.

**Defects found and fixed during verification (each with root cause +
regression coverage):**

1. `aura-sdk/pyproject.toml` declared `[project.dependencies]` as a table
   (invalid for setuptools) - the SDK could never build as a distribution.
   -> fixed to an array; clean_install_test.py now builds + installs both wheels.
2. `cryptography` (needed by TLS test-CA tooling) undeclared in dev extra -
   fresh-venv test collection failed. -> added to dev + clean-install test.
3. **Docker image lacked psycopg** (pip install . without [postgresql]) while
   compose.postgres.yaml requires it - the production multi-instance compose
   could not start. -> Dockerfile now installs .[postgresql].
4. **run_server ignored documented deployment env vars** (AURA_API_KEY,
   AURA_API_SECRET, AURA_API_TRUST_PROXY, AURA_API_ALLOW_PIPELINE, ...) - the
   pipeline was un-enable-able in containers and trust_proxy un-setable.
   -> run_server now honors all ServerConfig env vars.
5. **Multi-instance migration race**: two instances opening the same fresh PG
   catalog raced CREATE TABLE IF NOT EXISTS -> UniqueViolation crash.
   -> fixed with a PostgreSQL advisory lock; regression test opens 6 stores
   concurrently and passes.
6. **8 web dependency vulnerabilities** (6 high, 2 moderate) in aura-web
   build/dev transitive deps. -> npm audit fix; now 0.

**Claim status vs. prior reports:** prior claims were largely reproducible;
the defects above were not previously reported and were genuine gaps
discovered by fresh verification.

**Major remaining risks:** no alert-delivery platform wired (rules specced
only); TLS certs are operator-supplied (no public-CA automation); audit falls
back to a bounded buffer during store outage; single-region PG rate limiting;
no production-scale multi-node load test - only controlled local/staging.

**Final classification: B - PRODUCTION CANDIDATE** (see section J).
## B. CLAIM VERIFICATION

Prior claims checked against repository + fresh verification evidence:

- PostgreSQL persistence, migrations, transactions, distributed sessions/keys/
  rate limiting, shared audit, multi-instance replay, backup/restore,
  production topology E2E, release gate: **VERIFIED**.
- TLS proxy: **VERIFIED** for LOCAL TEST TLS (5/5 tests); public production
  TLS **NOT RUN** (no CA issuance exercised).
- Load test: **PARTIALLY VERIFIED** (local/staging only).
- Container deployment: **PARTIALLY VERIFIED** — worked only after fixes 3-4;
  now 9/9 container lifecycle.
- Clean install: previously **unverifiable**; now Verified.
- Dependency security + SBOM: previously **unverified**; now Verified.

## C. CLEAN ENVIRONMENT RESULTS

Command: `python 06_SOURCE_CODE/evaluation/clean_install_test.py --with-tests`

- Fresh venv; wheels built from source; both installed with declared deps;
  import + SDK local-mode smoke passed; full suite passed (PG skipped).
- Result: CLEAN INSTALL VERIFICATION: PASSED.

## D. DEPLOYMENT RESULTS

- Docker build OK; container_verify.py **9/9** PASS.
- Compose (postgres + 2 API): both healthy on shared PG; memory on api-1
  visible on api-2.
- Multi-instance migration race fixed; TLS proxy 5/5 (local test TLS).

## E. SECURITY RESULTS

- Auth/authz pass; secrets clean; pip-audit 0, npm audit 0.
- Prompt-injection and fail-closed outage behavior pass.

## F. RELIABILITY RESULTS

- PG failure explicit; rollback; schema refusal; outage fail-closed;
  failover; migration race fixed; container restart.

## G. DISASTER RECOVERY RESULTS

- Backup/restore (PG) tested; upgrade (blank->v1, data preserved, future
  refused); rollback runbook documented (forward-only migrations honest).

## H. PERFORMANCE RESULTS

Smoke load: 383 RPS, p50 2.35ms, p95 64.8ms, p99 67.6ms, 0% errors.
Local/staging only.

## I. RELEASE ARTIFACTS

Wheels built+installed+smoke-tested; web built+tested+audit-clean; container
image lifecycle-tested; 2 CycloneDX SBOMs; ARTIFACT_MANIFEST.md.

## J. FINAL RELEASE DECISION

**Classification: B - PRODUCTION CANDIDATE.**

Evidence: real container lifecycle (9/9), real PostgreSQL + distributed state
across two instances, TLS-proxy (local test TLS), backup/restore + upgrade +
rollback, dependency security clean, SBOMs + artifacts smoke-tested.

Why not A: production-critical gates NOT RUN - public-TLS certificate
issuance, wired alert delivery, production-scale multi-node load, durable audit
replay after outage.

Blocking items for A: wire alerting, exercise a real CA + managed proxy, run a
production-scale load benchmark, add durable audit replay after outage.

Recommended next steps: (1) deploy behind managed TLS proxy with real CA;
(2) connect alerting to documented rules; (3) production-scale load test;
(4) address audit-outage durability; (5) schedule restore drills.