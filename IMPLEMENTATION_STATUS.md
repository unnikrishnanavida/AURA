# IMPLEMENTATION STATUS

Status labels: IMPLEMENTED / PARTIAL / INTERFACE READY / SCAFFOLD / BROKEN / DEPRECATED / HISTORICAL.

## Canonical integrated platform: 06_SOURCE_CODE/aura (STRONG)

| Domain | Status | Evidence |
|---|---|---|
| foundation | IMPLEMENTED | ids, errors, Result, clocks, lifecycle, cancellation, RNG, validation, serialization; tests |
| config | IMPLEMENTED | typed pydantic settings, defaults->file->env loader; tests |
| core | IMPLEMENTED | bootstrap, DI container, registry, lifecycle, health/readiness; tests |
| memory | IMPLEMENTED | working/episodic/semantic/procedural, provenance, confidence, graph, consolidation; tests |
| knowledge | IMPLEMENTED | claim/evidence/source, trust, verification, contradiction; tests |
| reasoning | IMPLEMENTED | 6 strategies + consensus + verification + uncertainty-first; tests |
| planning | IMPLEMENTED | decomposition, constraints, risk, compare; tests |
| execution | IMPLEMENTED | action models, world-state/action-input separation, checkpoint; tests |
| reflection | IMPLEMENTED | post-execution review, counterfactual reflection; tests |
| learning | IMPLEMENTED | validated signal gate, versioning, rollback, auth gate; tests |
| brain | IMPLEMENTED | cognitive orchestration, bounded loops; SDK/API tests |
| security | IMPLEMENTED | capabilities, permissions, safety, autonomy, budgets, recovery, audit, redaction, adaptive defense; tests |
| observability | IMPLEMENTED | logging, metrics, flight recorder, replay, provenance; tests |
| providers | IMPLEMENTED | provider profiles/registry + embedded deterministic provider; tests |
| research | IMPLEMENTED | ledger, claim passport, evidence provenance, hypotheses; tests |
| sdk | IMPLEMENTED | `from aura import Aura` typed client |
| api | IMPLEMENTED | health/ready/reason/replay/openapi thin routes; tests |
| cli | IMPLEMENTED | health/run/reason/plan/replay/version/config validate; verified |
| agents bridge | INTERFACE READY | adapts the guarded aura-agents runtime (optional extra) |

## Standalone repositories

| Repository | Status | Note |
|---|---|---|
| aura-agents | IMPLEMENTED | 92 tests pass; guarded agent runtime; 4 BOM files repaired this session |
| aura-brain | PARTIAL | 33 BOM files repaired; contracts/runtime compile; scaffold stubs remain |
| aura-execution-complete | IMPLEMENTED | controlled execution engine; dry-run runs |
| aura-research | IMPLEMENTED | research engine; tests pass |
| aura-reasoning(2) | STRONG/HISTORICAL | 583 real, import-clean; reference superset |
| aura_reasoning | STRONG/HISTORICAL | 488 real, import-clean; older reference |
| aura-security | IMPLEMENTED | adaptive-defense lifecycle tested (sandbox/approval/canary/rollback) |
| aura-api / aura-cli | INTERFACE READY | standalone scaffolds; canonical is aura/api & aura/cli |
| aura-core / aura-memory / aura-knowledge / aura-planning / aura-execution / aura-cloud / aura-desktop / aura-mobile / aura-sdk / aura-reflection / aura-learning | SCAFFOLD / HISTORICAL | auto-generated trees; canonical implementation is in aura/ (see KNOWN_LIMITATIONS) |
| aura-memory | BROKEN (auto-gen) | 5095 malformed generated files; superseded by aura/memory |
| aura-learning | BROKEN (auto-gen) | 163 malformed generated files; superseded by aura/learning |
| aura-web | PARTIAL | single module |
| benchmarks / evaluation / examples / replay / scripts / tests | REAL-UNTESTED | research/utility, no in-repo pytest config |

## Honest labels

- Nothing is marked IMPLEMENTED unless it runs and is exercised by tests or live CLI/API execution.
- Auto-generated broken trees are labeled BROKEN/HISTORICAL and superseded by the canonical `aura/`
  package; they are NOT regenerated as fake code (mission rule: no empty-file completion).
