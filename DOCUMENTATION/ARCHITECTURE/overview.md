# AURA Ecosystem — Architecture Overview

This document reflects the **verified** state of the ecosystem as of the final
completion pass. Labels used: IMPLEMENTED, PARTIAL, SCAFFOLD, HISTORICAL.

## Canonical runtime

The one authoritative integrated AURA runtime is:

```
06_SOURCE_CODE/aura/
```

It is a typed, tested Python package (`src/aura/*`) providing foundation, config,
core, memory, knowledge, reasoning, planning, execution, reflection, learning,
brain, security, observability, providers, research, sdk, api, cli, and an
agents bridge. It builds (`wheel` + `sdist`), ships Docker/compose/CI, and its
test suite passes.

## Lifecycle

```
INPUT -> OBSERVATION -> INTERPRETATION -> MEMORY -> KNOWLEDGE -> REASONING
  -> RESEARCH -> PLANNING -> SECURITY/AUTHORIZATION -> AGENTS/EXECUTION
  -> VERIFICATION -> REFLECTION -> VALIDATED LEARNING -> MEMORY CONSOLIDATION
  -> OBSERVABILITY/AUDIT/REPLAY -> NEXT CYCLE
```

## Repository roles (verified)

Standalone repositories under `06_SOURCE_CODE/` are *not* the runtime; they are
specialized engines / clients / scaffolds. Their canonical owners are listed in
`STATUS/ecosystem-status.md`.

| Repo | Role | State (this pass) |
|---|---|---|
| aura | canonical integrated runtime | IMPLEMENTED (tested, packaged) |
| aura-agents | strong guarded agent runtime | IMPLEMENTED (92 tests pass) |
| aura-research | research engine | IMPLEMENTED (3 tests pass) |
| aura-security | adaptive-defense engine | IMPLEMENTED (9 tests pass) |
| aura-execution-complete | controlled execution engine | IMPLEMENTED (2 tests pass) |
| aura-cloud | standalone cloud engine | PARTIAL (2 tests pass; simulated) |
| aura-desktop | desktop client architecture | PARTIAL (2 tests pass; shadow fixed) |
| aura-mobile | mobile client architecture | PARTIAL (2 tests pass; shadow fixed) |
| aura-core | reusable infrastructure | IMPROVING (kernel + 6 tests; logging shadow fixed) |
| aura-planning | flat-layout real modules | PARTIAL (packaging mismatch with tests) |
| aura-execution | flat-layout real modules | PARTIAL (packaging mismatch with tests) |
| aura-api / aura-cli | compatibility/interface layer | PARTIAL (scaffold-heavy) |
| aura-knowledge | scaffold | SCAFFOLD (0 real of 471) |
| aura-reflection | scaffold/partial | PARTIAL (56 real of 213) |
| aura-memory / aura-learning / aura_reasoning / aura-reasoning(2) | historical | HISTORICAL/SUPERSEDED |

## Boundaries

- Canonical `aura/` owns every cross-cutting concern (ids, errors, results,
  clocks, config, DI, health, security, observability).
- Standalone engines depend on nothing in the clients; the direction is
  `clients -> aura/ -> domain contracts -> optional engines`.
- No standalone repo is imported by the canonical runtime except through the
  opted-in `aura/agents` bridge.