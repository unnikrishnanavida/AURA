# Historical Components

Superseded or generated trees that are **NOT part of the supported runtime**.
Each carries an in-tree `STATUS.md`. They are preserved for reference only.

| Tree | Status | Why |
|---|---|---|
| `aura-memory` | HISTORICAL · SUPERSEDED | 5,095/5,338 broken auto-generated files; canonical is `aura/memory` |
| `aura-learning` | HISTORICAL · SUPERSEDED | 163 broken auto-generated files; canonical is `aura/learning` |
| `aura_reasoning` | HISTORICAL · GENERATED | 488 generated scaffolds (no validated logic); canonical is `aura/reasoning` |
| `aura-reasoning(2)` | HISTORICAL · GENERATED | 580 generated scaffolds + 32,447 dead branches; canonical is `aura/reasoning` |
| root `benchmarks/evaluation/examples/replay/scripts/tests` | GENERATED util | 100% generator-header modules, untested |

## Guidance

- Do **not** import any historical tree from supported runtime code.
- Do **not** "repair" generated boilerplate to inflate file counts.
- If a feature idea from a historical tree is genuinely valuable (e.g.
  calibration, causal graphs, symbolic/temporal reasoning), reimplement it from
  scratch in the canonical package **with tests**.