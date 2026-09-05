# REASONING CONSOLIDATION PLAN

## Context

There are three reasoning source trees in `06_SOURCE_CODE/`:

| Tree | Files | Real logic | Generated header | Dead-branch sig | Empty | Tests |
|---|---|---|---|---|---|---|
| `aura/src/aura/reasoning` (canonical) | 12 | **genuine** | 0 | 0 | 0 | unit tests (passed) |
| `aura_reasoning` | 488 | none | 488/488 | 0 | 0 | 4 files (scaffold) |
| `aura-reasoning(2)/aura_reasoning` | 488 | none | 488/488 | **32,447** | 3 | 9 files (scaffold) |

## Finding (corrected, verified)

Both standalone reasoning trees are **auto-generated scaffolding**, not strong logic.
They were produced by a code generator that emits a generic `State`/`Record`/`Graph`
dataclass trio and a bare "Domain-first implementation" header into every module.
`aura-reasoning(2)` additionally contains tens of thousands of **dead branches**
(`if "method_name" == "method_name":`) plus 3 empty modules (e.g.
`abduction/hypothesis/hypothesis_ranker.py` is 0 bytes).

My earlier classifier reported these as "REAL" because they contain code, but the code is
template boilerplate with no behavioral tests. They are NOT the evolution of a working engine.

The canonical `aura/src/aura/reasoning/` is the **only** genuinely implemented, tested reasoning
engine (uncertainty-first, consensus, verification, deductive/abductive/causal/probabilistic/
counterfactual/analogical strategies, with tests).

## Decision

1. **Authoritative reasoning engine = `aura/src/aura/reasoning/`.** Tested, typed, and what the
   SDK/API/Brain consume via `from aura import Aura`.

2. **`aura_reasoning` and `aura-reasoning(2)` are HISTORICAL / GENERATED SCAFFOLD.**
   Preserved on disk for reference only; not part of the runtime; not imported by any supported code.
   Treated like the aura-memory / aura-learning generated trees.

3. **No feature migration is warranted as-is.** The generated modules do not contain validated logic
   to port. If a specific idea from those trees is genuinely valuable (e.g. calibration, causal
   graphs, symbolic/temporal reasoning), it should be **reimplemented from scratch** in the canonical
   package with unit tests — not copied from the scaffold.

4. **Recommended follow-up:** archive both generated trees under a `historical/` area so active runtime
   trees contain only canonical code (see `FINAL_ECOSYSTEM_VERIFICATION.md`).
