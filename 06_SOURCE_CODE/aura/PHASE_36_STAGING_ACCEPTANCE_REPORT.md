# PHASE 36 — STAGING DEPLOYMENT AND EXTERNAL INTEGRATION ACCEPTANCE

- Date: 2026-09-27
- Workspace: `E:\AURA` · canonical runtime `E:\AURA\06_SOURCE_CODE\aura`
- Baseline HEAD: `3542e5bd` (`docs(release): final ecosystem acceptance`)
- Phase-36 commit: created at end of this report (see Git section)
- Mode: one bounded phase. **Phase 37 not started.**

---

## 1. Executive summary

Phase 36 took the accepted baseline (`3542e5bd`, 419/419 backend tests, no known
defects from Phase 28–35) and moved it from *locally accepted implementation* to
*independently exercised staging operation* where the environment permitted —
using a **real, isolated PostgreSQL 18.3 cluster**, the **unmodified canonical
code**, and **no fabricated credentials or infrastructure**.

What is now **verified** by live runs in this phase:

- Fresh-cluster deployment with automatic schema migration (v1 applied on empty
  staging DB).
- Startup, health/ready probes, authentication (401/201), reasoning, memory
  write + recall, audit durability **across a process restart** (a genuinely
  separate server process against the same staging DB).
- Real 429 rate limiting against the deployed server (exhaustion probe
  `[200, 200, 429, 429]`) and the two denials **durably audited**.
- Database backup → loss (truncate) → restore → **no-clobber protection**
  (rollback-safe restore gate) on the staging DB.
- Bounded HTTP load against the deployed server over real PostgreSQL:
  200 requests, **0 errors**, p95 = 115.4 ms (< 500 ms pre-set threshold),
  ~140.6 req/s — **THRESHOLD PASS** (local staging box, not production load).
- Full gate re-run green on the Phase-36 tree: backend **419/419 (exit 0)**,
  web vitest **16/16**, E2E **7/7**, clients **10/10**, mypy strict clean,
  ruff clean, `security_check.py` clean.

What remains **honestly BLOCKED / NOT VERIFIED** (no credentials or toolchains
present — nothing was invented):

- Live external providers (OpenAI/Ollama): no credentials → not exercised.
- Container runtime: Docker daemon down → container/HA/blue-green not run.
- Production TLS edge: no operator-issued certificates (TLS proxy mechanism is
  covered by the automated test-CA proxy tests within the 419).
- Browser-automated web E2E: no Playwright/Selenium in the venv.
- Desktop/mobile packaging + launch: no PyInstaller/Electron/mobile toolchains.

One operational incident was observed and resolved during this phase (see §7.6):
an external/background process mutated non-canonical working trees at
`06_SOURCE_CODE/aura-api` and `06_SOURCE_CODE/aura-agents` mid-phase; all
tracked content was restored from HEAD — zero committed content lost; the
canonical runtime was never affected.

**Release classification (updated, evidence-based):**

| Component | Phase 35 | Phase 36 |
|---|---|---|
| Backend core (canonical runtime) | Class C — staging ready | **Class C — staging ready** (now also backed by a verified isolated staging deployment + bounded load evidence). NOT promoted to B: containerized HA, live provider acceptance, production certified TLS edge, and scaled load remain unverified. |
| Full ecosystem (web + cloud + desktop + mobile + external deps) | Class D | **Class D** (unchanged; depends on credentials/toolchains/staging infra). |

---

## 2. Baseline inspection (Step 1)

Facts verified at phase start:

- Branch `main`; **HEAD `3542e5bd`** — matches the reported final-acceptance
  commit. `git log -12` shows the Phase 27–35 chain intact.
- Python: `.venv\Scripts\python.exe` 3.14.3; `import aura` →
  `E:\AURA\06_SOURCE_CODE\aura\src\aura` (canonical, no duplicate runtime).
- Working tree at start: **no tracked modifications**; only pre-existing
  untracked migration artifacts (`AURA_MIGRATION_*.md/.json`,
  `GIT_STATE_BEFORE_MIGRATION.txt`, `MIGRATION/`, `cpath_refs.txt`,
  `db_refs.txt`, `junction_list.txt`, `robocopy_L_inventory.txt`,
  `secret_scan_list.txt`, `venv_pip_freeze_migration.txt`,
  `06_SOURCE_CODE/pgtest_data/`). These were preserved untouched.
- Docs read: `FINAL_AURA_ECOSYSTEM_ACCEPTANCE_REPORT.md`,
  `docs/DEPLOYMENT_RUNBOOK.md`, `docs/ROLLBACK_RUNBOOK.md`,
  `docs/BACKUP_AND_RECOVERY.md`, `docs/SECURITY_OPERATIONS.md`,
  `docs/TESTING.md`, `docs/PERFORMANCE.md`, `docs/PROVIDERS.md` (locations
  verified on disk).
- No env credentials of any kind were present (see §4).

No acceptance criteria from Phases 27–35 were re-implemented or weakened.

---

## 3. Staging readiness inventory (Step 2)

| # | Item | Status | Evidence / notes |
|---|---|---|---|
| S1 | PostgreSQL + persistent storage | **AVAILABLE** | PostgreSQL 18.3 binaries (`initdb`/`pg_ctl`); dedicated isolated staging cluster; data destroyed at teardown |
| S2 | TLS / domain / certificate | **MISSING (LAB VERIFIED)** | No operator cert/domain; TLS proxy mechanism verified inside the automated suite (test-CA proxy tests) |
| S3 | Container runtime | **BLOCKED** | `docker ps` → daemon not running (`npipe … open //./pipe/dockerDesktopLinuxEngine … failed`) |
| S4 | Environment configuration & secret injection | **VERIFIED** | Production gates (`run_server` env parsing) executed in Phase 28; staging isolation documented in runbook; no secrets in this phase's outputs |
| S5 | Live provider credentials | **BLOCKED** | Env probe found no provider/cloud credential names at all (see §4) |
| S6 | Database migration and rollback | **VERIFIED** | Fresh-DB migration (`version=1` applied) on staging cluster; rollback-at-data-layer proven by restore drill incl. no-clobber gate (§5.5); app-level rollback procedures exist in `ROLLBACK_RUNBOOK.md` |
| S7 | Backup and restore | **VERIFIED** | Real export/truncate/restore on the staging DB (§5.5) |
| S8 | Logs, metrics, alert delivery | **VERIFIED (local) / operator-wired (alert)** | `/v1/metrics` probed (401 unauthenticated), observability gates in suite; real alert delivery remains operator-wired |
| S9 | Browser E2E tooling | **MISSING** | `playwright`/`selenium` not importable in the venv |
| S10 | Desktop/mobile build toolchains | **MISSING** | `PyInstaller` not installed; no Electron; mobile toolchains absent |
---

## 4. Live provider acceptance (Step 4)

- Environment probe for credential-bearing variable names
  (`OPENAI*`, `ANTHROPIC*`, `GEMINI*`, `GOOGLE_API*`, `GROQ*`, `AWS_*`,
  `AZURE_*`, `GOOGLE_APPLICATION*`) returned **NONE**.
- Per execution rule 6/9: no live provider test is claimed and none was run.
  The provider boundary, fallback, `provider_failure` single-emission
  telemetry, and no-secret-in-errors behavior remain covered by the automated
  suite (Phase 29 tests + E2E scenario G), which re-passed 419/419 in this
  phase.
- This item is classified **BLOCKED — external credentials required**;
  operator follow-up is documented in §9.

---

## 5. Staging deployment and staging E2E (Steps 3 and 5)

### 5.1 Environment used

- Canonical runtime (unmodified source install) `E:\AURA\06_SOURCE_CODE\aura`.
- Separate throwaway PostgreSQL 18.3 cluster: `initdb` + `pg_ctl` on
  `127.0.0.1:55499`, bound to loopback, `trust` auth **only within this
  throwaway**, data directory under `.agents` (removed at teardown).
- Dedicated staging database per round (`aura_staging`, `aura_staging_rt3`),
  empty at start; schema created by the application's own migration code.
- Throwaway staging API tokens (`staging-bearer-token-0001`,
  `staging-issuer-secret-…`) — masked in every output; not operator secrets.
- Staging secrets/data are isolated from any production system: no production
  system, DSN, certificate, or credential was used or referenced.

### 5.2 Deployment + write/read rounds (commands)

```
# 1) create + start isolated staging cluster
initdb -D E:\AURA\.agents\pgstaging_data -U postgres -A trust -E UTF8 --no-locale
pg_ctl -D E:\AURA\.agents\pgstaging_data -o "-p 55499 -h 127.0.0.1" -l .agents\pgstaging.log start

# 2) deploy canonical application against it (write round = fresh process)
$env:S36_DB='aura_staging_rt3'; python build/staging_driver.py write
# 3) restart = genuinely new server process, same staging DB
python build/staging_driver.py read
# 4) backup/restore drill + bounded HTTP load
python build/stage36_h2.py
# 5) teardown
pg_ctl -D E:\AURA\.agents\pgstaging_data stop -m fast
(delete .agents staging artifacts)
```

### 5.3 Write-round evidence (deployed server, live HTTP + real PG)

| Check | Result |
|---|---|
| GET /health | 200 |
| GET /ready | 200 |
| GET /v1/metrics without token | 401 |
| POST /v1/sessions (Bearer) | 201, session id `ses-973a4db8…` |
| POST /v1/reason (plain facts, no rules) | 200, answer `I do not know` (uncertainty-first; correct) |
| POST /v1/remember | 200, `mem-9876e76b…` |
| POST /v1/recall | 200, n=1 |
| GET /v1/audit (before any denial) | 200, n=0 |
| Rate-limit exhaustion (isolated tight-bucket server burst=2) | `[200, 200, 429, 429]` |

### 5.4 Restart persistence (read round, separate process)

| Check | Result |
|---|---|
| GET /health after restart | 200 |
| Memory recall across restart | 200, n=1 (row written pre-restart) |
| Audit across restart | 200, n=2 (the two 429 denials from 5.3 are durably audited) |
| `aura_api_keys` row count | 0 (throwaway tokens are not persisted) |
| Process exit code | **0** |

### 5.5 Backup / restore / rollback drill (real PG, staging DB)

| Check | Result |
|---|---|
| Rows before backup | 1 |
| Backup artifact | 825 bytes (custom `create_pg_backup`) |
| Simulate data loss (`TRUNCATE memory_entries, memory_archive`) | rows = 0 |
| Restore | `memory_entries` restored to 1 (`memory_archive` 0) |
| Second restore while target non-empty | **refused** — no-clobber / rollback-safety gate PASS |

Rollback semantics: data-layer rollback verified above; binary deploy rollback
procedures are documented in `docs/ROLLBACK_RUNBOOK.md`. A container-based
green/blue swap requires the container runtime (S3 = BLOCKED).

### 5.6 Inventory of Step-5 scenarios A–I

| Scenario | Where exercised | Result |
|---|---|---|
| A auth/session lifecycle | 5.3 (401/201) + suite | PASS |
| B API → reasoning + provider | 5.3 reason 200; E2E scenarios A/B (suite) | PASS |
| C memory across sessions/restarts | 5.4 (n=1) | PASS |
| D audit durability/spool/replay/query | 5.4 (audits durable); E2E scenario D (spool/replay) in suite | PASS |
| E authorization/rate-limit/security response | 5.3 (401, 429, denials audited); E2E scenario E (brute-force→incident) | PASS |
| F provider failure & recovery | E2E scenario G (provider failure→fallback) re-passed in 419/419 | PASS |
| G DB failure & recovery | E2E scenario F (DB down → spool → replay) re-passed in 419/419 | PASS |
| H backup/restore/rollback | 5.5 drill | PASS |
---

## 6. Performance and reliability (Step 6)

### 6.1 Thresholds (defined before running)

- Endpoint mix: `POST /v1/recall` (authenticated, real-PG-backed).
- Concurrency: 8 workers × 25 requests = **200 requests**.
- Acceptance: **p95 latency < 500 ms**, **error rate < 2 %**, **0 timeouts**.

### 6.2 Results (deployed server, threaded HTTP over real PG)

| Metric | Value |
|---|---|
| Requests | 200 |
| Duration | 1.422 s |
| Throughput | 140.6 req/s |
| p50 | 20.13 ms |
| **p95** | **115.38 ms** |
| p99 | 538.13 ms |
| max | 1018.52 ms |
| Error rate | 0.0 % (0 errors) |
| **THRESHOLD_PASS** | **True** |

### 6.3 Interpretation

This is **bounded local-staging load evidence** on one Windows host with a
loopback PostgreSQL and an un-tuned threaded server; it is NOT a substitute
for staged load/soak under a load generator, multi-instance deployment, or the
container orchestrator. The Phase-35 microbenchmarks were not re-run and are
not cited as staging evidence; the numbers above are new, live-HTTP numbers.
p95 is stable under the pre-set threshold.

---

## 7. Security, observability, recovery, and hygiene

- Authentication covered: bearer-missing → 401; exhaustion → 429; denials are
  **audit-logged** (n=2 after the probe) and survive restart.
- No credential material appears in any Phase-36 output: tokens were masked
  (`***MASKED***`); no secret was printed to logs/reports/terminal (outputs
  reviewed; `security_check.py` = "security scan ok").
- Attack surface unchanged; dependency vulnerability scans were **not
  re-run** in this phase (dependencies unchanged since the Phase-28 baseline;
  reference results at `3542e5bd`: pip-audit clean, npm audit 0, secret scan
  clean).
- Recovery items verified: restart (5.4), backup/restore/rollback (5.5),
  DB-failure spool/replay and provider-failure fallback (Step-5 matrix).

### 7.6 External working-tree mutation incident (operational note)

During Phase 36, a background/external process (not any Phase-36 command —
commands were audited; none touched these paths) removed tracked content at
`06_SOURCE_CODE/aura-api` and `06_SOURCE_CODE/aura-agents` and later re-created
untracked content under `aura-agents/` (e.g., `api/`, `autonomy/`, …). The
canonical runtime `06_SOURCE_CODE/aura` was **never** affected. Response:

1. Detected via an unexpected `git status` delta mid-phase.
2. All **tracked** deletions restored from `HEAD`
   (`git restore --source=HEAD`), so HEAD content is intact on disk;
   re-verified.
3. Untracked re-created content left untouched (preserved, not deleted).
4. The Phase-36 commit index was rebuilt narrowly (`git reset` + explicit
   `git add` of only Phase-36 files) so the commit cannot absorb any external
   mutation.

---

## 8. Client packaging status (Step 7)

| Client | Unit logic | Build/install/launch | Classification |
|---|---|---|---|
| Desktop (`aura.clients.desktop` + `secure_store` + `offline_queue`) | 10/10 tests pass (algorithm-identical to mobile) | No PyInstaller / Electron; no GUI host | **NOT BUILT / NOT VERIFIED** (toolchains MISSING) |
| Mobile (`aura.clients.mobile`) | Part of the 10/10 | No Android/iOS toolchains | **NOT BUILT / NOT VERIFIED** (toolchains MISSING) |
| OS keyring seam | logic tested via fake backend | `keyring` package not installed — live OS-keyring round-trip not executed | **NOT VERIFIED** |

Shared primitives (secure storage, offline queue, sync) are the same objects
verified by `tests/clients`. Packaging is honestly reported as not executed.

---

## 9. Known defects and blockers

1. **Live provider acceptance BLOCKED** — no operator/provider credentials.
   Follow-up: provide one real provider credential + run the Step-4 matrix
   (success, auth failure, timeout, rate limit, outage, fallback telemetry,
   secret-leak scan of logs).
2. **Containerized staging BLOCKED** — Docker daemon unavailable on this host.
   Container bring-up, multi-instance HA, health-check orchestration, and
   blue/green rollback remain **ENVIRONMENT DEPENDENT**.
3. **Production TLS edge MISSING** — no operator certificate/domain. The TLS
   proxy path is lab-verified via the automated test-CA proxy tests only.
4. **Browser web E2E NOT RUN** — Playwright/Selenium absent from the venv.
5. **Desktop/mobile launch NOT VERIFIED** — no packaging toolchains.
6. **Non-canonical trees externally mutating** during the phase (§7.6): fix is
   to stop external tooling writing into `E:\AURA\<non-canonical>` trees or
   move them out of the repository.
7. **Phase 36 stops here; Phase 37 requires explicit authorization.**

---

## 10. PASS / FAIL / BLOCKED / NOT RUN matrix

| Requirement | Status |
|---|---|
| Baseline inspection + preflight | **PASS** (HEAD `3542e5bd` matched; docs present; gates re-run green) |
| Staging readiness inventory (11 items) | **PASS** (each labeled AVAILABLE/MISSING/BLOCKED/VERIFIED, §3) |
| Isolated staging deployment (real PG, migrations, restart, persistence) | **PASS** |
| Deployment rollback verification | **PASS** (data-layer restore + no-clobber gate; binary rollback documented) |
| Backup + restore on real PG | **PASS** |
| Security: auth, authorization, rate limiting, audit durability | **PASS** |
| DB failure → spool → replay | **PASS** (in 419-suite scenario F) |
| Provider failure → fallback + telemetry | **PASS** (in 419-suite scenario G) |
| Bounded staging load with pre-set thresholds | **PASS** (p95 115 ms < 500 ms; 0 errors) |
| Live external provider acceptance | **BLOCKED** (no credentials) |
| Container runtime / HA bring-up | **BLOCKED** (daemon down) |
| Production TLS edge with real certs | **NOT RUN** (no certificate; lab-only) |
| Browser web E2E (scenario I) | **NOT RUN** (no toolchain) |
| Desktop/mobile packaging + launch | **NOT RUN** (no toolchains) |
---

## 11. Updated release classification (with justification)

- **Backend core — Class C (STAGING READY), retained.** Justification: an
  isolated staging deployment of the **unmodified** canonical runtime now has
  live evidence for fresh-DB migration, deployment, probes, restart
  persistence, audit durability, rate limiting, backup/restore/rollback, and
  bounded HTTP load at 0 errors with p95 well under threshold. Promotion to
  Class B (production ready) is **not** justified: no operator TLS
  certificate, no containerized HA, no live-provider acceptance, no scaled
  load/soak evidence.
- **Full ecosystem — Class D (NOT READY), retained.** Live providers, real
  cloud, packaged desktop/mobile, browser-automated web, and containerized
  deployment all remain dependent on external credentials/toolchains
  classified MISSING/BLOCKED above.

Nothing in Phase 36 asserts 100% completeness or production readiness.

---

## 12. Exact commands and outcomes (summary)

| Command | Outcome |
|---|---|
| `initdb` + `pg_ctl` (isolated cluster `:55499`) | cluster up, then torn down at teardown |
| `python build/staging_driver.py write` | health/ready 200, 401 gate, session 201, reason 200, remember/recall 200, rate probe `[200,200,429,429]` |
| `python build/staging_driver.py read` (second process, same DB) | memory n=1, audit n=2, exit 0 |
| `python build/stage36_h2.py` | LOAD + BACKUP drill, THRESHOLD_PASS True |
| `python -m pytest -q` | 419/419, exit 0 |
| `python -m pytest tests/e2e -q` | 7/7 |
| `python -m pytest tests/clients -q` | 10/10 |
| `python -m mypy src` | Success: no issues (138 files) |
| `python -m ruff check src tests scripts` | clean (after the mechanical fix in §13) |
| `python scripts/security_check.py` | "security scan ok" |
| `npm test` (aura-web) | 16/16 |

The staging driver/loader scripts live under `06_SOURCE_CODE/aura/build/`
which is gitignored; they are evidence tooling, not shipped code.

---

## 13. Git

- Baseline: `main` @ `3542e5bd`.
- Phase-36 commit contains exactly:
  1. `06_SOURCE_CODE/aura/tests/e2e/test_scenarios.py` — mechanical lint fix
     (import ordering + 3 forward-reference annotation quote removals) to
     satisfy the project's own configured `I`/`UP` rules under the drifted
     ruff 0.16.x; **no test logic changed**; re-passed 7/7 before commit.
  2. This report.
  3. `CHANGELOG.md` — Phase-36 entry.
  4. `docs/DEPLOYMENT_RUNBOOK.md` — "Local isolated staging" playbook section
     (Phase-36 verified).
- Untracked artifacts (pre-existing migration docs, externally re-created
  boundary content, `pgtest_data`) remain untracked and are reported, not
  committed.
- Tree re-verified immediately before and after commit; `git status` results
  recorded in §14.