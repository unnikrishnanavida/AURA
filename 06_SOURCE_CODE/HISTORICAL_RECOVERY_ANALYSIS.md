# AURA Historical Repository Recovery Analysis

> Companion to Phases 5–8. This document is the authoritative disposition record
> for the historical AURA trees. The canonical integrated runtime is
> `06_SOURCE_CODE/aura/`; nothing in the supported runtime imports these trees.

## Method

Every repository was audited with the same workflow:

1. File inventory + byte-size distribution.
2. Python syntax compilation check (`ast.parse`) over all `.py` files.
3. Import-graph inspection for references to non-existent modules.
4. Search for generator fingerprints (`aura_learning.runtime`, `MODULE_FILE`,
   generic `ModuleService`, dead `if "method" == "method"` branches).
5. Comparison against the canonical runtime modules that already own the concepts.

The classifier script lives at `scripts/classify_historical_repos.py`.

## Classification legend

| Class       | Meaning                                              |
| ----------- | ---------------------------------------------------- |
| A. REAL     | Authored, internally consistent, behaviorally meaningful |
| B. PARTIAL  | Some useful concepts, not production runnable        |
| C. DUP      | Concept duplicated by the canonical runtime          |
| D. GENERATED| Emitted by a template generator                      |
| E. BROKEN   | Does not compile or imports non-existent modules     |
| F. OBSOLETE | Replaced/superseded; retained only as historical record |

## 1. `aura-memory` — 5 338 Python files

| Metric             | Value            |
| ------------------ | ---------------- |
| Files parsed OK    | 243              |
| Files failing parse| 5 095 (95.5 %)   |
| STATUS.md          | "HISTORICAL — SUPERSEDED" |

**Classification: E (broken), D (generated), F (obsolete).**

- `create_aura_memory_files.py` / `build_aura_memory_structure.py` produced the
  tree; generated files frequently contain unterminated literals and no valid
  Python, hence the 95 % syntax failure rate.
- The local `memory/core/{constants,exceptions,models,schemas,types,__init__}.py`
  modules parse and contain generic dataclass scaffolding (`State`/`Record`
  trios) without behavior or tests — **B (partially useful at best)**.

### Concept recovery

The concept tree (episodic/semantic/working/contextual/long-term memory,
consolidation, decay/forgetting, associations, versioning, retrieval,
provenance) is **C (duplicated)** by the canonical `aura/memory` engine, which
implements all of it **better**: multi-axis confidence, provenance, graph links,
consolidation, forgetting policy, replay-to-memory, and passing unit tests.

**Disposition: superseded.** No code migrated. Concept coverage verified against
`aura/src/aura/memory/`.

## 2. `aura-learning` — 4 925 Python files

| Metric         | Value |
| -------------- | ----- |
| Files parse OK | 4 925 |
| Ref to missing `aura_learning.runtime` | 1 561 |

**Classification: D (generated), E (broken).**

- Every module carries the generator header `typed B integration surface` and a
  `ModuleService` facade that imports `aura_learning.runtime`, which ships
  nowhere in the tree — 1 561 broken imports.
- The orchestrated surface (`learn(key, payload)`, runtime
  start/stop/`learn`) is a generic passthrough and performs **no learning**.

### Concept recovery

Feedback processing, outcome evaluation, policy improvement, calibration,
error analysis, and regression protection are owned by canonical
`aura/learning` (validation gate, authorization for safety-relevant changes,
versioned registry, rollback) and `aura/reflection`.

**Disposition: superseded.** No code migrated. The learning **loop** (observe →
evaluate → signal → validate → apply → monitor → rollback) was implemented in
the canonical runtime (`aura/learning/loop.py`) during Phase 5.

## 3. `aura_reasoning` — 488 Python files

**Classification: D (generated), F (obsolete).** Its own `STATUS.md` declares
the tree "GENERATED SCAFFOLD — NOT SUPPORTED RUNTIME". All modules parse but
carry the same generator header and no behavioral tests.

### Concept recovery

Claims, assumptions, evidence, inference, hypothesis, uncertainty,
calibration, provenance, decomposition, synthesis, and conclusion are already
first-class in `aura/src/aura/reasoning/` (assumptions, inference steps,
traces, consensus, verification, six strategies) and `aura/src/aura/research/`
(epistemic statuses EVIDENCE/INFERENCE/HYPOTHESIS/SPECULATION, claim passports,
contradictions).

**Disposition: superseded.** No code migrated. `ReasoningInput` already accepts
`assumptions`; `ReasoningResult` carries structured `Conclusion` objects which
distinguish strategy/statement/confidence/uncertainty/support/alternatives.

## 4. `aura-reasoning(2)` — 583 Python files

| Metric | Value |
| ------ | ----- |
| Files parse OK | 580 (3 empty) |
| Dead `if "method"=="method"` branch lines | ~93 046 |
| STATUS.md | self-declared GENERATED SCAFFOLD |

**Classification: D (generated), F (obsolete), E (partially broken).** Dead
branch volume and 3 empty modules confirm non-functional generation.

**Disposition: superseded.** Same recovery path as `aura_reasoning`.

## Migration candidates (selected)

| Source concept | Migration status | Target |
| -------------- | ---------------- | ------ |
| episodic/semantic/working memory + associations | Superseded by canonical | `aura/memory` (already richer) |
| consolidation / decay / forgetting | Superseded by canonical | `aura/memory/consolidation.py`, `engine.enforce_forgetting` |
| feedback → policy improvement | Superseded by canonical + newly implemented loop | `aura/learning` |
| calibrated uncertainty / claim statuses | Superseded by canonical | `aura/reasoning/uncertainty.py`, `aura/research/models.py` |

## Additional scaffolds: `aura-brain`, `aura-execution-complete`

`aura-brain` is a non-valid TOML scaffold (no build-system or package layout);
the canonical brain engine lives at `aura/src/aura/brain/`. The canonical
`aura.brain.BrainEngine` is the authoritative cognitive orchestrator.
`aura-execution-complete` contains a minimal smoke-suite and is superseded by
`aura/src/aura/execution/`. Both are archived/historical artifacts.

| Repo                   | Status                          | Canonical owner               |
| ---------------------- | ------------------------------- | ----------------------------- |
| `aura-brain`           | obsolete scaffold (invalid TOML)| `aura/src/aura/brain/`        |
| `aura-execution-complete` | historical scaffold        | `aura/src/aura/execution/`    |

## Outcome

No historical code was migrated into the canonical runtime. Where the mission
called for capabilities the historical trees merely named, the capability was
implemented or verified in the canonical runtime with tests (memory lifecycle
correction/versioning/sensitivity, learning loop, API/SDK/web integration).
This honors the rule: *a smaller amount of excellent code is preferable to
thousands of generated files*.