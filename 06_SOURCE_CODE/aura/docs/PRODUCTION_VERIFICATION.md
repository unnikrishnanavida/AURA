# AURA Production Verification (Phases 17-24 independent verification)

This document summarizes what the independent verification mission actually
proved, with exact artifacts and commands. See
`06_SOURCE_CODE/INDEPENDENT_PRODUCTION_VERIFICATION_REPORT.md` for the full
report, claim-by-claim tables, and the final release decision.

## Result

- Release gate (with live PostgreSQL + Docker): **40/40 PASSED**
  (`scripts/verify_ecosystem.py`, `AURA_TEST_POSTGRESQL_DSN` set).
- Clean install from source (fresh venv, wheels only): **PASSED**
  (`evaluation/clean_install_test.py`).
- Container lifecycle build->start->health->auth->pipeline->persist->restart +
  2-instance compose topology: **9/9 PASSED** (`evaluation/container_verify.py`).
- Dependency security: pip-audit **0 vulnerabilities**, npm audit **0
  vulnerabilities** (evidence in `release/security/`).
- SBOMs: CycloneDX 1.6 for Python (80 components) and web (350 components) in
  `release/sbom/`.

## Capability detection

Infrastructure-coupled gates report **NOT RUN** (not FAIL) when the dependency
is absent: PostgreSQL unreachable, Docker daemon down, pip-audit missing.
This is implemented in `verify_ecosystem.py` (pg reachability probe, `docker
info` probe). A release classification must still discount NOT RUN
production-critical gates — see the report's section J.

## What was fixed during verification

1. `aura-sdk` pyproject dependencies array (was invalid for setuptools).
2. Declared `cryptography` dev dependency (TLS test-CA tooling).
3. Dockerfile missing `[postgresql]` extra (production compose could not start).
4. `run_server` ignored deployment env vars (`AURA_API_KEY`, `AURA_API_SECRET`,
   `AURA_API_TRUST_PROXY`, `AURA_API_ALLOW_PIPELINE`, ...).
5. Multi-instance migration race fixed with a PostgreSQL advisory lock.
6. Resolved 8 web dependency vulnerabilities (npm audit fix).

## Gate checklist (Phase 24)

| # | Gate | Status |
| - | ---- | ------ |
| 1 | clean install | PASSED |
| 2 | build (wheels + fresh install) | PASSED |
| 3 | tests (canonical + SDK + web + standalone) | PASSED |
| 4 | lint / type check | PASSED |
| 5 | import validation | PASSED |
| 6 | PostgreSQL | PASSED (real PG 18.3 + compose postgres:16) |
| 7 | migrations | PASSED (upgrade tests) |
| 8 | persistence restart | PASSED |
| 9 | distributed state | PASSED |
| 10 | TLS | PASSED (local test TLS only) |
| 11 | container deployment | PASSED |
| 12 | security tests | PASSED |
| 13 | secret scan | PASSED |
| 14 | dependency scan | PASSED |
| 15 | SBOM generation | PASSED |
| 16 | backup | PASSED |
| 17 | restore | PASSED |
| 18 | upgrade | PASSED |
| 19 | rollback | DOCUMENTED (runbook; forward-only migrations) |
| 20 | load test | PASSED (local/staging smoke) |
| 21 | chaos/failure tests | PASSED |
| 22 | production topology E2E | PASSED (12/12) |
| 23 | release artifact smoke test | PASSED |
| 24 | rollback verification | DOCUMENTED |

NOT RUN / NOT APPLICABLE items (documented, not marked passed): public-TLS
certificate issuance, wired alert delivery, production-scale multi-node load,
durable audit replay after store outage.