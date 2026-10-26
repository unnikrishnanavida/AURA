# AURA Verification Playbook (Phase 39)

Reproducible commands for every supported quality gate. Run from the canonical
runtime root unless noted. The canonical interpreter is the repo venv
(`E:\AURA\.venv` in this checkout; substitute `<VENV>/Scripts/python`).

## Backend gates

```bash
<VENV>/python -m pytest tests/execution tests/learning   # SRC-1 + Scenario H + learning e2e
<VENV>/python -m pytest tests/config/test_provider_config.py   # provider-config determinism
<VENV>/python -m pytest tests/execution/test_path_resolution_security.py  # supplementary (non-symlink)
<VENV>/python -m pytest                                      # full backend suite
<VENV>/python -m mypy src                                     # strict type check
<VENV>/python -m ruff check src tests                          # lint
```

## Live PostgreSQL (isolated throwaway cluster; never point at production)

```bash
# 1. create an isolated cluster (PostgreSQL 18+ binaries on PATH)
initdb -D <tmp>/data -U aura -A trust -E UTF8
pg_ctl -D <tmp>/data -l <tmp>/server.log start -w -o "-p 55432 -h 127.0.0.1"
# 2. run the PG-gated + full suite
export AURA_TEST_POSTGRESQL_DSN="host=127.0.0.1 port=55432 dbname=postgres user=aura"
<VENV>/python -m pytest tests/memory/test_pg_store.py tests/memory/test_pg_upgrade.py \
    tests/memory/test_pg_concurrent_migration.py tests/observability/test_pg_backup.py \
    tests/security/test_audit_durable.py tests/api/test_distributed.py tests/api/test_multi_instance.py
<VENV>/python -m pytest
# 3. teardown (test databases are auto-dropped per-module)
pg_ctl -D <tmp>/data stop -m fast
```

## Web gates

```bash
cd aura-web
npm install          # first time
npm test             # vitest unit tests
npm run lint         # eslint
npm run build        # tsc -b && vite build
```

## Browser acceptance gates (real Chrome + real API, no fakes)

```bash
# backend first, then:
cd aura
<VENV>/python scripts/browser_e2e.py          # sign-in -> reasoning -> real answer; exit 0
<VENV>/python scripts/viewport_acceptance.py  # shell + drawer at 1440/1280/768/390
<VENV>/python scripts/research_graph_acceptance.py  # populated Research + Knowledge Graph; exit 0
```

Each script starts a fresh `AuraApiServer` (8765) and Vite (5210), signs in
through the real UI, drives real pages headlessly, and asserts: no uncaught
page errors, no console errors, no horizontal overflow, and real backend data
rendered. Screenshots land in `build/` (`browser_e2e.png`,
`viewport_*_<W>x<H>.png`, `research_graph_<desktop|mobile>_<W>x<H>.png`).
Accepts `AURA_WEB_DIR` to point at the web checkout if it is not adjacent.

## CLI smoke

```bash
<VENV>/python -m aura.cli.main ready
<VENV>/python -m aura.cli.main security status
<VENV>/python -m aura.cli.main doctor
```

## Optional / environment-gated

- **Live provider (requires operator credential):** set `AURA_PROVIDER_API_KEY`
  (or an OpenAI-compatible `OPENAI_API_KEY`) and
  `AURA_STORAGE_POSTGRESQL_DSN`-style provider config via `config/env/*.yaml`;
  no live call is made without it. Never put secrets in a committed file.
- **Local Ollama:** install Ollama, `ollama pull <model>`, ensure
  `http://127.0.0.1:11434` is reachable, then configure
  `provider: {enabled: true, kind: ollama, base_url: ..., model: ..., privacy_approved: true}`.
- **Desktop/mobile:** platform toolchains required (PyInstaller/Electron/Android
  SDK); the clients are zero-dependency Python packages and only unit-tested here.

## Known environment limitations at Phase 39

- Symlink-escape test skips on Windows without symlink privilege; run
  `pytest tests/execution/test_secure_actions.py` on a capable host/CI.
- PostgreSQL-gated tests skip unless `AURA_TEST_POSTGRESQL_DSN` is set.
- Docker, live-provider, TLS-edge, and packaging gates are
  environment-blocked (see `PHASE_39_FINAL_INTEGRATION_AND_RELEASE_READINESS.md`).
  Browser-automated web acceptance is **not** blocked: Playwright + Chrome are
  available in this environment and the gates in "Browser acceptance gates"
  above are passing.