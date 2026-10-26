# PHASE 44 — TARGETED BLOCKER CLOSURE & RELEASE ACCEPTANCE

Follow-up to PHASE_43. Canonical runtime `E:\AURA\06_SOURCE_CODE\aura` ·
Git root `E:\AURA` · `main @ dc2d32d3` · **no commit, no push, no deployment**.

## A. Executive summary
Targeted closure phase: re-verified the Phase 43 baseline on the current
checkout, added a **real junction-escape security test** that passes on this
host (literal symlink test still skipped for lack of privilege), ran a
**controlled 3-run performance repeat**, re-ran the full regression on a fresh
isolated PostgreSQL cluster, inspected the desktop artifact without executing
it, and recorded explicit scope decisions for live-provider and Docker.

## B. Declared release scope (unchanged)
Local development ✅ · Local testing ✅ · Desktop packaging (build) ✅ ·
Staging runbook ⚠️ · Production ❌ · Mobile NOT REQUIRED.
**Scope decision (C):** the selected local-first release does NOT require a live
AI provider (embedded deterministic provider is the default; offline adapter
tests pass) nor a container runtime (staging runbook uses local processes).
Both are **NOT REQUIRED FOR SELECTED RELEASE SCOPE** with those justifications;
criteria documented in case the operator expands scope.

## C. Environment inventory
Windows 10 (10.0.26200) · Python 3.14.3 venv · Node 24.18.0 · Chrome +
Playwright + PyInstaller 6.22.3 + psycopg present · Docker CLI only (daemon
absent) · Ollama down · PostgreSQL 18.3 binaries · no TLS cert · symlink
privilege absent but **NTFS junction creation available**.

## D. Workstream results
| Workstream | Status | Evidence |
|---|---|---|
| A Symlink-escape | **PARTIAL → improved** | literal `os.symlink` still skips (errno 22); **junction-escape test PASSES** (new `test_junction_escape_rejected` — NTFS junction inside workspace pointing outside is rejected by `Workspace.resolve`; external file untouched). Full suite 480 incl. junction. |
| B Desktop executable | **PARTIAL** | artifact inspected via `pyi-archive_viewer` (contains `desktop_launcher` + bundled modules; no secrets visible). Build + Python launcher PASS. **Launch blocked by host Application Control** (recorded; not bypassed). |
| C Live provider / Docker | **NOT REQUIRED** for selected scope | decision + justification above |
| D Staging/Production | PARTIAL / NOT READY | runbook exists; operator cert + infra required |
| E Performance | PASS (bounded, controlled) | 3-run repeat below |
| F Regression/e2e | PASS | full suite 480/1; browser E2E re-passed |

## E. Junction-escape security test (new this phase)
`tests/execution/test_secure_actions.py::test_junction_escape_rejected` creates
a real NTFS junction in the managed workspace pointing at an outside directory
and verifies (1) any read through it is denied with `escapes workspace`,
(2) the outside file is never modified. Passed on this host — genuine runtime
evidence of the same `Path.resolve()` confinement used for symlinks.

## F. Performance follow-up (controlled 3-run repeat, in-process real API)
| Run | req/s | p50 ms | p95 ms | max ms | errors | exec_count | rate_deny |
|---|---|---|---|---|---|---|---|
| 1 | 176.6 | 21.7 | 48.0 | 536 | 0 | 200 | 0 |
| 2 | 239.5 | 14.8 | 29.9 | 520 | 0 | 200 | 0 |
| 3 | 244.2 | 10.6 | 36.2 | 521 | 0 | 200 | 0 |

Every run: 200 requests / 8 threads, exact `execution_count=200` correlation,
zero errors, zero rate-limit denials. Variation (176–244 req/s) is bounded host
noise (Application-Control scanning, thread scheduling) on an in-process server;
first-request max ~520 ms is warm-up. **Not a production capacity claim**; a
dedicated benchmark with fixed conditions is recommended for any SLA.

## G. Regression acceptance (exact commands, current checkout)
- `pytest tests/execution/test_secure_actions.py tests/execution/test_path_resolution_security.py` → **23 passed, 1 skipped** (symlink)
- Full `pytest` with fresh isolated PostgreSQL 18.3 (port 55432, torn down) → **480 passed, 1 skipped** (symlink)
- `scripts/browser_e2e.py` → **exit 0 · BROWSER_E2E_OK**
- `pytest tests/api/test_api.py` → 19 passed · `mypy src` → 139 files clean · `ruff check src tests scripts` → all passed · web `npm test` 16/16 · lint/build OK
- `pyi-archive_viewer -l dist/aura-desktop-smoke.exe` → artifact structure verified (no execution)
- Cluster teardown verified (stopped, dir removed)

## H. Security & governance
Verified controls unchanged (default-deny, gates, budgets, timeouts/cancel,
allowlist shell=False, confinement incl. **junction-escape**, output caps, HMAC,
rate limits, request caps, audit/spool, CORS, redaction, governed learning,
live-PG isolation/replay). Unproven: OS sandbox, hacking immunity, production
TLS, live provider, OS-keyring runtime, containerized HA, literal-symlink
escape on this host. Application Control treated as authoritative.

## I. Capability matrix (established equal-weight 23-item method, unchanged)
Implementation coverage **23/23**. Operational verification **20/23 (~87%)** —
path-security depth improved by the junction test but capability statuses are
unchanged; partials: desktop launch, mobile, live provider; deployment partial.

## J. Readiness by release target
Local development **READY** · Local testing **READY** · Desktop packaging
**READY (build + artifact inspection)**; runtime launch **BLOCKED (OS policy)** ·
Staging **PARTIAL** (operator cert/infra) · Production **NOT READY** · Mobile
**NOT REQUIRED** · Live provider & Docker **NOT REQUIRED for selected scope**.

## K. Resolved blockers (this phase)
Path-security: junction escape-vector now **verified on the current host**
(literal symlink test remains environment-skipped).

## L. Remaining blockers & exact next operator actions
1) Code-sign or admin-approve the desktop EXE (then launch acceptance).
2) Run literal-symlink test on a symlink-capable host/CI.
3) If scope expands: provider credential or local Ollama+model; Docker Desktop;
operator TLS cert + DNS/proxy for staging/production edge.
4) Production acceptance demands operator infra: deployment, TLS, load,
monitoring/alerting, backup/restore, rollback, security review.

## M. Git & artifact hygiene
`main @ dc2d32d3` · staged 0 · deleted 0 · modified tracked **22** (unchanged)
· untracked **77** (58 pre-existing + prior ours + `scripts/performance_probe.py`
+ Phase-43 report + Phase-44 report; `tests/execution/test_secure_actions.py`
remains an untracked our-file, edited in place). `dist/` and `build/`
gitignored; `.pg44` removed. No commit, push, tag, publish, or deployment.