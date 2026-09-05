# STATUS: HISTORICAL — GENERATED SCAFFOLD — NOT SUPPORTED RUNTIME

> **Do not use this tree.** It is retained for historical/reference purposes only.

## Why this tree exists
This is an auto-generated scaffold tree produced by a code generator that emits a
generic `State` / `Record` / `Graph` dataclass trio and a bare
"Domain-first implementation" header into every module.

## Why it is not the runtime
All 488 modules carry the generator header; none has behavioral tests. The
generated code is template boilerplate, not validated reasoning logic.

## What replaces it (authoritative implementation)
Use the canonical, tested reasoning engine:

    **06_SOURCE_CODE/aura/src/aura/reasoning/**

It implements uncertainty-first reasoning, explicit confidence, assumptions,
consensus, verification, and the six strategies (deductive, abductive, causal,
probabilistic, counterfactual, analogical), with passing unit tests, and is what
the SDK/API/Brain consume via `from aura import Aura`.

## Which package developers should use
- AUTHORITATIVE: `06_SOURCE_CODE/aura/src/aura/reasoning/`
- THIS TREE: HISTORICAL — do not import. Nothing in the supported runtime imports it.
