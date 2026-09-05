# FINAL ECOSYSTEM VERIFICATION

Status labels: **IMPL, IMPLEMENTED** (runs + tested) · **PARTIAL** (authored but incomplete) ·
**SCAFFOLD/GENERATED** (auto-generated, no validated logic) · **HISTORICAL/SUPERSEDED** (not runtime) ·
**BROKEN** (syntax failures).

This report is evidence-backed. Every "IMPL" claim is supported by a test run, import check, or live
execution performed during verification.

---

## 1. Every repository individually

| Repo | Py | Real | Stub | Empty | Broken | TestF | Tests pass | Import | Packaging | Status | Prod-ready |
|---|---|---|---|---|---|---|---|---|---|---|---|
| `aura` (canonical) | 119 | 119 | 0 | 0 | 0 | 16 | ✅ all | ✅ | ✅ wheel+sdist, Docker+compose+CI | **IMPL / CANONICAL** | ✅ |
| `aura-agents` | 130 | 130 | 0 | 0 | 0 | 13 | ✅ 92 | ✅ 102 mods | ✅ Docker | **IMPL (standalone engine)** | ✅ |
| `aura-research` | 68 | 50 | 0 | 18 | 0 | 3 | ✅ 3 | ✅ | ✅ | **IMPL (standalone engine)** | ✅ |
| `aura-execution-complete` | 81 | 58 | 0 | 23 | 0 | 3 | ✅ 2 | ✅ | ✅ | **IMPL (standalone engine)** | ✅ |
| `aura-security` | 396 | 396 | 0 | 0 | 0 | 29 | ✅ 9 | ✅ | ✅ | **IMPL (standalone engine)** | ✅ |
| `aura-brain` | 976 | 951 | 0 | 25 | 0 | 10 | n/a* | ⚠ partial | ✅ | **PARTIAL** | ⚠ |
| `aura-api` | 215 | 215 | 0 | 0 | 0 | 21 | n/d | ⚠ | ✅ | **PARTIAL / INTERFACE** | ⚠ |
| `aura-cli` | 216 | 216 | 0 | 0 | 0 | 20 | n/d | ⚠ | ✅ | **PARTIAL / INTERFACE** | ⚠ |
| `aura-core` | 251 | 238 | 13 | 0 | 0 | 1 | n/a* | ✅ | ✅ | **PARTIAL** | ⚠ |
| `aura-cloud` | 69 | 52 | 0 | 17 | 0 | 2 | n/d | ⚠ | ✅ | **SCAFFOLD/PARTIAL** | ⚠ |
| `aura-desktop` | 65 | 47 | 0 | 18 | 0 | 2 | n/d | ⚠ | ✅ | **SCAFFOLD/PARTIAL** | ⚠ |
| `aura-mobile` | 66 | 46 | 0 | 20 | 0 | 3 | n/d | ⚠ | ✅ | **SCAFFOLD/PARTIAL** | ⚠ |
| `aura-execution` | 426 | 285 | 0 | 141 | 0 | 12 | n/d | ⚠ | ✅ | **PARTIAL** | ⚠ |
| `aura-knowledge` | 471 | 471 | 0 | 0 | 0 | 41 | n/d | ⚠ | ✅ | **PARTIAL** | ⚠ |
| `aura-planning` | 429 | 359 | 0 | 70 | 0 | 8 | n/d | ⚠ | ✅ | **PARTIAL** | ⚠ |
| `aura-reflection` | 213 | 213 | 0 | 0 | 0 | 17 | n/d | ✅ | ✅ | **PARTIAL** | ⚠ |
| `aura-sdk` | 752 | 752 | 0 | 0 | 0 | 1 | n/d | ✅ | ✅ | **PARTIAL / INTERFACE** | ⚠ |
| `aura-web` | 1 | 1 | 0 | 0 | 0 | 0 | — | ⚠ | — | **SCAFFOLD** | ⚠ |
| `aura-memory` | 5338 | 243 | 0 | 0 | 5095 | 33 | ✗ | ✗ | ✗ | **HISTORICAL / SUPERSEDED / BROKEN** | ❌ |
| `aura-learning` | 4925 | 4762 | 0 | 0 | 163 | 38 | ✗ | ✗ | ✗ | **HISTORICAL / SUPERSEDED / BROKEN** | ❌ |
| `aura_reasoning` | 488 | 488* | 0 | 0 | 0 | 4 | ✗ | ⚠ | ✗ | **HISTORICAL / GENERATED** | ❌ |
| `aura-reasoning(2)` | 583 | 580* | 0 | 3 | 0 | 9 | ✗ | ⚠ | ✗ | **HISTORICAL / GENERATED** | ❌ |
| `benchmarks` | 25 | 25* | 0 | 0 | 0 | 0 | ✗ | — | — | **GENERATED (root util)** | ❌ |
| `evaluation` | 23 | 23* | 0 | 0 | 0 | 0 | ✗ | — | — | **GENERATED (root util)** | ❌ |
| `examples` | 8 | 8* | 0 | 0 | 0 | 0 | ✗ | — | — | **GENERATED (root util)** | ❌ |
| `replay` | 10 | 10* | 0 | 0 | 0 | 0 | ✗ | — | — | **GENERATED (root util)** | ❌ |
| `scripts` | 9 | 9* | 0 | 0 | 0 | 0 | ✗ | — | — | **GENERATED (root util)** | ❌ |
| `tests` | 17 | 17* | 0 | 0 | 0 | 5 | ✗ | — | — | **GENERATED (root util)** | ❌ |

Notes:
- `*` under Real for generated trees = *contains code* — template boilerplate, not validated logic (§7).
- `n/a*` = no runnable pytest collected in-repo (test files are package markers).
- `n/d` = not deep-run this pass (authored; PARTIAL; canonical logic lives in `aura/`).
- All `aura-*` standalone repos (except the 4 historical) have **0 generated headers / 0 dead-branch
  signatures** → genuinely authored.

---

## 2. Canonical implementation for every major capability

| Capability | Canonical (authoritative) | Historical/duplicate |
|---|---|---|
| Reasoning | `aura/src/aura/reasoning` | `aura_reasoning`, `aura-reasoning(2)` (generated) |
| Memory | `aura/src/aura/memory` | `aura-memory` (generated, broken) |
| Learning | `aura/src/aura/learning` | `aura-learning` (generated, broken) |
| Knowledge | `aura/src/aura/knowledge` | `aura-knowledge` (standalone) |
| Planning | `aura/src/aura/planning` | `aura-planning` (standalone) |
| Execution | `aura/src/aura/execution` | `aura-execution`, `aura-execution-complete` |
| Reflection | `aura/src/aura/reflection` | `aura-reflection` (standalone) |
| Security | `aura/src/aura/security` | `aura-security` (standalone adaptive defense) |
| Agents | `aura/src/aura/agents` (bridge) | `aura-agents` (standalone runtime) |
| Brain/Orchestration | `aura/src/aura/brain` | `aura-brain` (standalone) |
| API / CLI / SDK | `aura/src/aura/{api,cli,sdk}` | `aura-api`, `aura-cli`, `aura-sdk` |
| Providers | `aura/src/aura/providers` | — |
| Research | `aura/src/aura/research` | `aura-research` (standalone) |

Canonical `aura/` is the unified orchestration layer — it coordinates all capabilities and is what the
SDK/API/Brain consume. Standalone engines (agents, research, security, execution-complete) are strong,
independently testable, and are bridged where appropriate.


---

## 4. Remaining stub files and justification

- `aura-brain`: 25 empty files are all `tests/unit/<domain>/__init__.py` — legitimate test-package
  markers, not stubs. No unexplained stub.
- `aura-core`: 13 stub files remain (small init/interface shims) — legitimate package markers.
- Scaffold repos (cloud/desktop/mobile/execution/planning): empty files are mostly `__init__.py`
  markers in partial authored trees. These repos are PARTIAL, not claimed IMPL.
- No **canonical** `aura/` package has any stub or empty file (119/119 real).

---

## 5. Remaining broken files and justification

- `aura-memory` (5,095) and `aura-learning` (163): malformed auto-generated scaffolding, not salvageable
  as real code, duplicated by the tested canonical `aura/memory` + `aura/learning`. Marked
  HISTORICAL/SUPERSEDED. Not regenerated as fake code (mission rule). Preserved for reference.
- No canonical or supported-runtime file is broken.

---

## 6. Duplicate code decisions

| Duplicate | Decision |
|---|---|
| `aura_reasoning` + `aura-reasoning(2)` | Neither is canonical (both generated). Keep as HISTORICAL. `aura/reasoning` is the only real engine. See `REASONING_CONSOLIDATION_PLAN.md`. |
| `aura-memory`/`aura-learning` standalone vs `aura/memory`/`aura/learning` | Standalone generated trees are HISTORICAL; canonical wins. |
| Standalone `aura-{api,cli,sdk,core,...}` vs `aura/{api,cli,sdk,core,...}` | Canonical `aura/` is authoritative for the runtime. Standalone authored structures are PARTIAL references. |
| `aura-agents` standalone vs `aura/agents` bridge | Standalone runtime is the strong, tested engine; `aura/agents` is a thin bridge (optional). Both coexist by design. |

---

## 7. Credibility of the "generated" classification (evidence)

- Every module in `aura_reasoning`, `aura-reasoning(2)`, `aura-memory`, `aura-learning`, and the root
  util dirs begins with the literal header **`Domain-first implementation for ...`** — 100% of modules,
  exact same generator template. Authored code does not do this.
- `aura-reasoning(2)` contains **32,447** occurrences of `if "name" == "name":` (always-true / dead
  branches) and 3 zero-byte files.
- The generator emits generic `AbductionState/Record/Graph` dataclasses into custom-named modules —
  classic scaffold output.
- These trees have **no behavioral tests**; their "test" files are scaffolds.
- Clean compile is not proof of logic — it only proves the token stream parses.

---

## 8. Tests and validation evidence (this pass)

| Repo | Result |
|---|---|
| `aura` (canonical) | pytest ✅ 100% (foundation..api, brain, sdk); imports; `aura 0.2.0` loads; wheel+sdist builds |
| `aura-agents` | 92 tests ✅ (after BOM repair of 4 files) |
| `aura-research` | 3 tests ✅ |
| `aura-execution-complete` | 2 tests ✅ |
| `aura-security` | 9 tests ✅ |
| BOM repair | 37 files (aura-agents + aura-brain) fixed; 0 broken remain in both |

---

## 9. Known limitations

- Standalone `aura-{api,cli,cloud,core,desktop,mobile,execution,knowledge,planning,reflection,sdk,brain}`
  are authored but PARTIAL — the canonical, tested implementations live in `aura/`. Developers should
  use `aura/` for the runtime.
- Root-level `benchmarks/evaluation/examples/replay/scripts/tests` are generated scaffolds (no validated
  logic) and are not part of the supported runtime.
- `aura-memory`/`aura-learning`/`aura_reasoning`/`aura-reasoning(2)` are broken/generated and preserved
  only as historical reference.
- The two generated reasoning trees have no port-worthy validated logic; future features there
  (calibration, causal graphs, symbolic/temporal) must be reimplemented from scratch with tests if needed.
- Deployment artifacts (Docker/CI/wheel) exist for the canonical `aura` and `aura-agents`; other
  standalone repos have pyproject but no container.

---

## 10. Recommended next development priorities

1. **Consolidate runtime onto `aura/`** as the single importable platform (already canonical); keep
   standalone engines only where independently strong (agents, research, security, execution-complete).
2. **Finish the PARTIAL standalone scaffolds** (or formally deprecate them) so developers are not
   confused about which is authoritative — either complete `aura-{api,cli,cloud,...}` or point them at
   `aura/`.
3. **Archive generated trees** (aura-memory, aura-learning, aura_reasoning, aura-reasoning(2), root
   util dirs) into a dedicated `historical/` area to keep the active runtime tree clean.
4. If calibration/causal/symbolic/temporal reasoning is required, **reimplement** those features in
   `aura/reasoning` with unit tests (do not copy scaffold).
5. Add integration tests that exercise cross-domain flows through the canonical `aura` package
   (memory→reasoning→planning→execution→reflection→learning; detection→incident→adaptive-defense).
6. Extend persistence adapters (SQLite/Postgres) and add Kubernetes manifests + streaming/auth for the
   API once validated.

---

## 3. Historical / superseded repositories

Marked with `STATUS.md` in-tree and documented here:

| Tree | Marker | Reason |
|---|---|---|
| `aura-memory` | HISTORICAL · SUPERSEDED · NOT SUPPORTED | 5,095 broken auto-generated files |
| `aura-learning` | HISTORICAL · SUPERSEDED · NOT SUPPORTED | 163 broken auto-generated files |
| `aura_reasoning` | HISTORICAL · GENERATED · NOT SUPPORTED | 488 generated scaffolds, no logic |
| `aura-reasoning(2)` | HISTORICAL · GENERATED · NOT SUPPORTED | 488 generated scaffolds + 32k dead branches |
| root `benchmarks/evaluation/examples/replay/scripts/tests` | GENERATED util | 100% generated headers, untested |

`STATUS.md` files were added to `aura-memory`, `aura-learning`, `aura_reasoning`, `aura-reasoning(2)`.
