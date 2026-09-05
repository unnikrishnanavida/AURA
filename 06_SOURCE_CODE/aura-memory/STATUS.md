# STATUS: HISTORICAL — SUPERSEDED — NOT SUPPORTED RUNTIME

> **Do not use this tree.** It is retained for historical/reference purposes only.

## Why this tree exists
This is an auto-generated scaffold tree for AURA memory, produced by a code generator.

## Why most generated files are broken
5,095 of 5,338 `.py` files fail syntax compilation. The generator wrote out
bare text as the first line (no `#` comment), left broad strings, and produced
unterminated literals, so the files are not valid Python. These are artifacts of
the generation process, not authored code.

## What replaces it (authoritative implementation)
Use the integrated, tested memory engine in the canonical platform:

    **06_SOURCE_CODE/aura/src/aura/memory/**

This is the real implementation used by the runtime: `from aura import Aura` →
`aura.remember(...)` / `aura.recall(...)`. It provides working/episodic/semantic/
procedural memory with provenance, confidence, graph links, consolidation, and
replay-to-memory, and has passing unit tests.

## Which package developers should use
- AUTHORITATIVE: `06_SOURCE_CODE/aura/src/aura/memory/`
- THIS TREE: HISTORICAL — do not import. Nothing in the supported runtime imports it.
