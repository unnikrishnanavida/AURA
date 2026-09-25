# Changelog

## [0.2.0] — 2026-Q3

### Phase 34 — Mobile Product (2026-09-25)

- `aura.clients.mobile.MobileClient` — offline-first mobile client on the SAME
  tested primitives as desktop: secure auth storage (Android Keystore / iOS
  Keychain seam via `SecureStore`), idempotent offline queue, `reason()` online
  or queued, `sync()` on reconnect, `SyncSnapshot` (pending/sequence/LWW).
- `tests/clients` 10/10 pass; mypy strict + ruff clean. Android/iOS
  build/launch classified **ENVIRONMENT DEPENDENT / NOT VERIFIED** (no mobile
  toolchains).
- Report: `06_SOURCE_CODE/aura/PHASE_34_MOBILE_PRODUCT_REPORT.md`.

### Phase 33 — Desktop Product (2026-09-25)

- New `aura.clients` thick-client foundation: **secure storage** (memory/env/OS
  keyring; never plaintext; refuses to degrade), **offline queue** (durable,
  idempotent, LWW, failure reporting), and **desktop client** (lifecycle +
  online/offline operation with secure auth and reconnect `sync()`).
- `tests/clients` 6/6 pass; mypy strict + ruff clean. GUI/packaging/launch
  classified **ENVIRONMENT DEPENDENT / NOT VERIFIED** (not built here).
- Report: `06_SOURCE_CODE/aura/PHASE_33_DESKTOP_PRODUCT_REPORT.md`.

### Phase 32 — Real Cloud Deployment Support (2026-09-25)

- New `aura.cloud` provider abstraction + policy/safety layer: `CloudManager`,
  `CloudClient` contract, `SimulatedCloudClient` (deterministic local
  lifecycle), cost budget, instance caps, IAM least-privilege guard, audit,
  and honest per-operation verification flags (`SIMULATED` / `LIVE: NO`).
- **No cloud credentials were available — every execution is SIMULATED** and
  explicitly flagged; live deployment classified **NOT VERIFIED /
  ENVIRONMENT_DEPENDENT**.
- `tests/cloud` 6/6 pass; mypy strict + ruff clean.
- Report: `06_SOURCE_CODE/aura/PHASE_32_REAL_CLOUD_DEPLOYMENT_REPORT.md`.

### Phase 31 — Web Productization (2026-09-25)

- Added a real **sign-in gate** (verify against `/ready`, 401 credential
  errors, session indicator, Sign out) and a **conversation** view (history,
  loading with Cancel via transport abort, per-turn Retry, safe structured
  answers incl. Phase-29 provider metadata). `AuraApi.request` gained external
  `AbortSignal` cancellation.
- Web suite: **16/16 tests pass** (auth 4 + conversation 3 + existing 9);
  `tsc -b && vite build` clean; eslint clean. Live browser E2E classified
  **NOT VERIFIED** (no browser automation toolchain).
- Report: `06_SOURCE_CODE/aura-web/PHASE_31_WEB_PRODUCTIZATION_REPORT.md`.

### Phase 30 — Canonical Ten-Layer Security (2026-09-25)

- Implemented the missing canonical controls (previous layers were already
  real and tested): **incident response** (`security/incident.py` — lifecycle,
  severity, evidence, escalation, audit), **threat detection** (`security/threats.py`
  — brute-force / rate-abuse / privilege-violation detectors → incidents),
  **privacy** (`security/privacy.py` — classification, allowlist redaction,
  retention, safe purge guidance), **encryption** (`security/encryption.py` —
  Fernet via `cryptography`, key management, rotation, no plaintext fallback),
  and **compliance readiness** (`security/compliance.py` — controls, evidence,
  status, audit history; no certification claims).
- Ten layers mapped to canonical implementation in
  `06_SOURCE_CODE/aura/PHASE_30_CANONICAL_TEN_LAYER_SECURITY_REPORT.md`.
- Negative tests: illegal lifecycle transitions, de-escalation, threat
  thresholds, redaction drops, encryption rotation/missing-key failure.
- mypy strict clean; ruff clean; full suite green.

### Phase 29 — Canonical Provider Runtime Integration (2026-09-25)

- The canonical reasoning path (SDK → Brain → Reasoning) now genuinely enters
  **one** provider boundary (`ProviderManager` + single `ProviderRegistry` with
  profile AND runtime instances) instead of a dead abstraction.
- Safe structured synthesis: after consensus + verification, an evidence-backed
  outcome may be polished by a policy-approved synthesis provider; contested /
  insufficient / uncertain results are never overridden (uncertainty-first
  preserved). Provider receives conclusions + verification only — never hidden
  chain-of-thought.
- Real HTTP adapters (OpenAI-compatible + Ollama) with credential-safe,
  transport-injectable clients; live calls classified **NOT VERIFIED** (no
  external credentials available).
- `provider_failure` metric now fires at the real boundary (metrics + audit +
  usage), exactly once per failure; failures fall back to the deterministic
  path, never propagate.
- Config: `ProviderConfig` (enabled/kind/base_url/model/api_key/timeout/
  privacy_approved), `SecretStr` redacted in safe dumps; `AURA_PROVIDER_*` env.
- Tests: provider manager, remote adapter (injected transport), reasoning
  synthesis, brain end-to-end — all pass; runtime verification against a real
  local HTTP endpoint (+ closed-endpoint failure path) passed.
- Full detail: `06_SOURCE_CODE/aura/PHASE_29_CANONICAL_PROVIDER_RUNTIME_REPORT.md`.

### Phase 28 — Production Baseline Acceptance (2026-09-25)

- Verified from evidence: clean install (isolated venv; wheel build + install;
  CLI `doctor`/`config validate`/`run`; API startup/health/auth/operation/
  shutdown/restart with data retained), canonical-path audit (**0** stale
  `C:\Users\navid` references across all 16,909 tracked files), TLS edge +
  two-instance PostgreSQL topology (live cross-instance sessions/memory/limits
  over HTTP), security baseline, release security (`pip-audit` clean after
  upgrading pip 25.3→26.2.1, `npm audit` 0, repo secret scan clean,
  CycloneDX SBOM with 78 components), and real PostgreSQL + SQLite
  backup/restore drills.
- **Findings fixed** (each with a regression test):
  - P28-1/P28-3 — clean shutdown: `AuraApiServer.close()` releases the memory
    store and the distributed-state pool (SQLite WAL lock + pool threads).
  - P28-2 — `load_settings()` ignored `AURA_*` env vars; the CLI now honors the
    same layered config as the API server.
  - P28-5 — `create_pg_backup` crashed on a fresh backup directory; it now
    creates it.
  - `scripts/security_check.py` now detects `eval`/`exec` via the AST (real
    Call nodes) so quoted markers such as the prompt-injection literals are not
    misreported.
- **359/359** tests pass (full suite incl. real-PostgreSQL integration);
  mypy strict clean; ruff clean.
- Full detail: `06_SOURCE_CODE/aura/PHASE_28_PRODUCTION_BASELINE_ACCEPTANCE_REPORT.md`.

### Phase 27 — Durable Audit + Production Reliability (2026-09-25)

- Audit records now carry a stable `event_id`
  (`aura.security.audit.AuditRecord`, backed by
  `aura.foundation.ids.EventId`); `GET /v1/audit` includes it.
- `PostgreSQLAuditLog` (`aura.api.distributed`) persists idempotently
  (`ON CONFLICT (event_id) DO NOTHING`) to `aura_audit_events`; the schema is
  upgraded in place (column add + deterministic backfill + unique index) under
  an advisory lock, so fresh and pre-existing deployments are both handled.
- Store-outage behavior is now durable: while PostgreSQL is unreachable a
  record stays observable in a bounded in-memory buffer **and** is spooled to
  local JSON-lines files (`aura.security.spool.AuditSpool`,
  `data/audit_spool/spool.jsonl`). `replay_spooled()` resyncs the spool
  idempotently after recovery and clears it only on full success.
- Audit query surface extended: `entries(...)` supports `event_id`, `actor`,
  `decision`, `action`, `correlation_id`, `since`, and `limit` filters, plus
  `count()`; local buffer + spool are served (deduplicated, never fabricated)
  during an outage.
- Fixed a latent `**payload` name-collision bug: `record(..., payload={...})`
  previously bound `{"payload": {...}}`; the API now accepts an explicit
  `payload` mapping (merged with flat extra keyword payloads).
- New tests: `tests/security/test_audit_spool.py` (5), 
  `tests/security/test_audit_durable.py` (11 failure-path unit tests),
  DSN-gated real-PostgreSQL integration tests in
  `tests/api/test_distributed.py`. Verified: full suite **356/356 pass**
  (exit 0) against a real PostgreSQL 18 cluster, mypy strict clean, ruff clean.
- Full detail: `06_SOURCE_CODE/aura/PHASE_27_DURABLE_AUDIT_REPORT.md`.

- Added the **integrated AURA platform** package at `06_SOURCE_CODE/aura`:
  foundation, config, core, memory, knowledge, reasoning, planning,
  reflection, learning, brain orchestration, security, observability,
  providers, SDK, API, CLI, Docker, compose, CI/CD, and 100+ tests.
- Consolidated the architecture baseline: earlier generated engine scaffolds
  are documented as historical source areas; the supported public surface is
  the integrated package.
- See `06_SOURCE_CODE/aura/CHANGELOG.md` for the per-package history.

## 0.1.0

- Initialized the AURA repository structure and scaffolded core documentation.
