# STATUS: HISTORICAL — SUPERSEDED — NOT SUPPORTED RUNTIME

> **Do not use this tree.** It is retained for historical/reference purposes only.

## Why this tree exists
This is an auto-generated scaffold tree for AURA learning, produced by a code
generator (the README itself contains literal `\n` escape text, evidence of the
generator output).

## Why most generated files are broken
163 `.py` files fail syntax compilation: they duplicate `from __future__ import
annotations` mid-file (after other statements), which is a hard `SyntaxError`,
and several carry ~83 KB of repeated template bodies.

## What replaces it (authoritative implementation)
Use the integrated, tested learning engine in the canonical platform:

    **06_SOURCE_CODE/aura/src/aura/learning/**

This is the real implementation used by the runtime. It implements the controlled
pipeline `observation -> candidate signal -> validation -> approved signal ->
controlled update`, with versioning, provenance, rollback, and an authorization
gate that blocks unauthorized safety-relevant changes. It has passing unit tests.

## Which package developers should use
- AUTHORITATIVE: `06_SOURCE_CODE/aura/src/aura/learning/`
- THIS TREE: HISTORICAL — do not import. Nothing in the supported runtime imports it.
