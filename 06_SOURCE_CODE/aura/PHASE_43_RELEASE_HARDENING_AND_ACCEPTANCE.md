# PHASE 43 — RELEASE HARDENING AND ACCEPTANCE

Follow-up to PHASE_42. Canonical runtime `E:\AURA\06_SOURCE_CODE\aura` ·
Git root `E:\AURA` · `main @ dc2d32d3` · **no commit, no push, no deployment**.

## A. Executive summary
Phase 42's verified baseline was re-confirmed on the current checkout (HEAD
unchanged, no source edits since). The new acceptance evidence produced this
phase is a **bounded local performance/operational probe** of the real HTTP API.
No regression was found and no code was changed except one new probe script and
two lint cleanups in existing scripts. All previously documented external
prerequisites remain unchanged.

## B. Declared release scope
Local development ✅ · Local testing ✅ · Desktop packaging (build) ✅ ·
Staging runbook ⚠️ · **Production ❌** · Mobile **NOT REQUIRED** for this scope.

## C. Environment inventory (no secrets)
Windows 10 (10.0.26200) · Python 3.14.3 (venv) · Node 24.18.0/npm 11.16.0 ·
Chrome + Playwright + PyInstaller 6.22.3 + psycopg present · Docker CLI only
(daemon absent) · Ollama down · PostgreSQL 18.3 binaries (isolated clusters) ·
TLS: no operator cert · Symlink privilege: absent (errno 22).

## D. Workstream status matrix
| Workstream | Status | Evidence |
|---|---|---|
| A Live AI provider | BLOCKED | no credentials; Ollama down; deterministic offline tests pass |
| B Docker/containers | BLOCKED | CLI only, daemon absent |
| C TLS/staging edge | PARTIAL | local ephemeral-CA handshake tests pass (full suite); no operator cert |
| D Desktop packaged app | PARTIAL | build + source/Python launcher PASS; EXE launch blocked by host Application Control (recorded, not bypassed) |
| E Mobile | NOT REQUIRED | out of selected release scope; zero-dep Python client only |
| F Symlink/path security | PARTIAL | traversal suite PASS; symlink-escape test skips (no privilege) |
| G Performance/operational | **PASS (bounded, local)** | fresh probe results below |
| H Regression/e2e acceptance | PASS | browser E2E + full suite re-run (below) |

## E. Exact commands and results (current checkout)
- `pytest tests/api/test_api.py` → **19 passed** (CORS regression incl.)
- `scripts/browser_e2e.py` → **exit 0 · BROWSER_E2E_OK** (real Chrome + API + vite)
- Full suite with fresh isolated PostgreSQL 18.3 (port 55432, loopback, torn down) → **479 passed, 1 skipped** (symlink privilege)
- `scripts/performance_probe.py` (NEW, G) → **PERF requests=200 errors=0**
  - run 1: 302.0 req/s · p50 2.9 ms · p95 18.8 ms · max 515 ms
  - run 2: 149.4 req/s · p50 29.6 ms · p95 63.2 ms · max 1038 ms
  - both runs: `execution_count=200` and `rate_limit_deny=0` (exact observability
    correlation; server torn down each run)
- `mypy src` → Success (139 files) · `ruff check src tests scripts` → All checks passed
- Web `npm test` 16/16 · `lint` clean · `build` success · CLI `ready` smoke OK

## F. Performance measurements and limitations
Bounded local load (200 req / 8 threads) against the real `/v1/reason` path with
the embedded deterministic provider and in-memory store: 0 errors, no
rate-limit denies, sub-100 ms p95 in both runs. **Limitations:** in-process
server + in-memory backend; NOT staged PG-backed load and NOT a production
sufficiency claim. No documented project load target is being replaced.

## G. Security and governance
Verified this env: default-deny policy, capability/safety/autonomy gates,
budgets, timeouts/cancellation, allowlisted shell=False execution, workspace
confinement, output caps, HMAC keys, rate limits, request caps, durable audit +
spool, CORS boundary (regression-tested), secret redaction, governed learning
auth/rollback, live-PG isolation/replay, observability correlation under load.
Unproven: OS sandboxing, hacking immunity, production TLS, live-provider
security, browser/OS-keyring secrets, containerized HA, symlink-escape runtime.
Host Application Control was authoritative and never bypassed (even the mypy
subprocess on one invocation was host-policy blocked; the authoritative `mypy
src` gate passed).

## H. Capability matrix (established equal-weight 23-item method)
Implementation coverage **23/23**. Operational verification **20/23 (~87%)** —
unchanged from Phase 42 (no capability newly toggled; performance probe is
enforcement evidence, not a new capability). Partials: desktop binary launch,
mobile, live provider; deployment partial. Method and weights unchanged.

## I. Readiness by release target
Local development **READY** · Local testing **READY** · Desktop packaging
**READY (build)**; runtime launch **BLOCKED by OS policy** · Staging
**PARTIAL (runbook; operational/TLS validation pending operator cert)** ·
Production **NOT READY** · Mobile **NOT REQUIRED FOR SELECTED SCOPE**.

## J. Resolved blockers
None newly resolved (all Phase 42 resolutions re-confirmed). No regression
found.

## K. Remaining blockers and exact operator prerequisites
1) Provider credential or local Ollama + model → run live inference matrix.
2) Docker Desktop/daemon → container multi-instance validation.
3) Operator TLS cert + DNS/proxy → staging/production edge validation.
4) Code-signing or admin-approved policy path for the desktop EXE launch.
5) Symlink-capable host/CI for the escape test.
6) Production load/deployment/monitoring/rollback acceptance (operator infra).

## L. Repository and artifact hygiene
`main @ dc2d32d3` · staged 0 · deleted 0 · modified tracked **22** (unchanged) ·
untracked **76** = 58 pre-existing + prior ours + `scripts/performance_probe.py`
+ this report. Generated/ignored artifacts untouched (`dist/`, `build/`,
`.pg*` cleaned). No commit, push, tag, publish, or deployment occurred.