# AURA Ecosystem Status

Verified status as of the final completion pass. Labels:
**IMPLEMENTED** (runs + tested) · **PARTIAL** (authored but incomplete) ·
**SCAFFOLD** (planned files only) · **HISTORICAL/SUPERSEDED** (not runtime).

## Canonical components (tested evidence)

| Component | Repo | Status | Evidence |
|---|---|---|---|
| Integrated runtime | `06_SOURCE_CODE/aura` | IMPLEMENTED | 100% tests; wheel/sdist; Docker/CI; `import aura` OK, v0.2.0 |
| Agent runtime | `06_SOURCE_CODE/aura-agents` | IMPLEMENTED | 92 tests pass |
| Research engine | `06_SOURCE_CODE/aura-research` | IMPLEMENTED | 3 tests pass |
| Security adaptive defense | `06_SOURCE_CODE/aura-security` | IMPLEMENTED | 9 tests pass |
| Execution engine | `06_SOURCE_CODE/aura-execution-complete` | IMPLEMENTED | 2 tests pass |
| Cloud engine | `06_SOURCE_CODE/aura-cloud` | PARTIAL | 2 tests pass (simulated provider) |

## Partial components

| Repo | Status | Notes |
|---|---|---|
| aura-core | IMPROVING | real kernel + 6 tests added; stdlib-logging shadow fixed |
| aura-desktop | PARTIAL | authored, 2 tests pass; `app.py` shadow fixed |
| aura-mobile | PARTIAL | authored, 2 tests pass; `app.py` shadow fixed |
| aura-planning | PARTIAL | real flat-layout modules; package mismatch with tests |
| aura-execution | PARTIAL | real flat-layout modules; package mismatch with tests |
| aura-api | PARTIAL | auth/rate-limit real; most modules scaffold |
| aura-cli | PARTIAL | formatters/security real; most modules scaffold |

## Scaffold components

| Repo | Real/Total | Notes |
|---|---|---|
| aura-knowledge | 0/471 | 100% TODO scaffold; canonical is `aura/knowledge` |
| aura-reflection | 56/213 | mostly scaffold; canonical is `aura/reflection` |

## Historical / superseded components

| Repo | Status |
|---|---|
| aura-memory | HISTORICAL (5,095 broken generated files) |
| aura-learning | HISTORICAL (163 broken generated files) |
| aura_reasoning | HISTORICAL (488 generated scaffolds) |
| aura-reasoning(2) | HISTORICAL (488 generated + 32k dead branches) |

Each historical tree carries a `STATUS.md` in-repo and is not imported by the
runtime.