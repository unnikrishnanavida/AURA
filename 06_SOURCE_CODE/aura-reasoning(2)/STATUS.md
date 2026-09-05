# STATUS: HISTORICAL — GENERATED SCAFFOLD — NOT SUPPORTED RUNTIME

> **Do not use this tree.** It is retained for historical/reference purposes only.

## Why this tree exists
This is an auto-generated scaffold tree (`aura_reasoning` package) produced by a
code generator. Higher module count than `aura_reasoning` is due to splitting
the same generated code across more files plus **32,447 dead branches**
(`if "method_name" == "method_name":`) and 3 empty modules
(e.g. `abduction/hypothesis/hypothesis_ranker.py` is 0 bytes).

## Why it is not the runtime
All 488 modules carry the generator header; the code is template boilerplate with
no behavioral tests. The dead branches and empty files confirm it is not a
working engine.

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
