# AURA Testing

How AURA is verified. Every claim maps to an executable path; nothing here is
aspirational.

## Layers

| Layer | Location | Notes |
|-------|----------|-------|
| Unit | `tests/*` (foundation, config, core, memory, knowledge, reasoning, planning, execution, security, observability, providers, clients, cloud, sdk, api, brain) | Pure logic, policies, serialization, algorithms |
| Integration | `tests/api/test_distributed.py`, `tests/memory/test_pg_store.py`, `tests/memory/test_pg_upgrade.py`, `tests/api/test_multi_instance.py`, `tests/observability/test_pg_backup.py` | Real PostgreSQL; DSN-gated (`AURA_TEST_POSTGRESQL_DSN`); disposable databases |
| End-to-end | `tests/e2e/test_scenarios.py` | Scenarios A–G against the canonical runtime (auth→reason→provider→audit, memory persistence, evidence→answer→provenance, planning+authorization, security→incident, DB failure→spool→replay, provider failure→fallback) |
| Failure | `tests/security/test_audit_durable.py`, `tests/observability/test_pg_backup.py`, Phase-28 drills | Simulated store death, torn spools, restore/no-clobber gates |
| Security | `tests/security/*`, `tests/api/test_tls_proxy.py` | 401/403/429, injection, defense pipeline, incidents, encryption rotation/missing-key |
| Web | `aura-web` vitest (+ `tsc -b`, eslint) | API client, components, auth gate, conversation (cancel/retry) |
| Web browser | `scripts/browser_e2e.py`, `scripts/viewport_acceptance.py`, `scripts/research_graph_acceptance.py` | Real Chrome vs. a fresh `AuraApiServer` + Vite: sign-in through the UI, reasoning answer, 4-viewport shell/drawer, populated Research + Knowledge Graph; asserts no page/console errors, no overflow |

## Running

```bash
# full suite (PG-gated tests skip unless a DSN is set)
python -m pytest tests -q

# with real PostgreSQL
set AURA_TEST_POSTGRESQL_DSN=host=127.0.0.1 dbname=postgres user=postgres
python -m pytest tests -q

# web
cd aura-web && npm test && npm run build && npm run lint
```

## Static gates

- `ruff check src tests scripts` — clean.
- `mypy src` (strict) — clean.
- `python scripts/security_check.py` — AST-based eval/exec detection + secret
  patterns — clean.
- `python scripts/validate_deployment.py production --storage=sqlite` →
  valid with a production secret; fails-closed otherwise.

## Test-state honesty

- PG-gated suites run against disposable databases (created/dropped per
  module) and NEVER against live data.
- Failure tests simulate store defects deliberately and assert observable
  fallback (spool, metric, audit) — they do not weaken assertions.
- 359+ tests collected; numbers are recorded per phase report at commit time.