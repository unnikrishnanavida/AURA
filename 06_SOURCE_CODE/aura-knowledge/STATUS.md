# STATUS: aura-knowledge

## Architectural role
AUTHORITATIVE standalone knowledge & evidence subsystem (claims, evidence,
sources, provenance, verification, trust, confidence, uncertainty,
contradiction, freshness, belief revision, retrieval).

## Canonical owner
`aura/src/aura/knowledge` (canonical runtime `aura/`). This repo is a
standalone subsystem that integrates with the canonical runtime through an
explicit adapter (`aura_knowledge.integrations.aura_canonical`) — it does NOT
duplicate the canonical engine.

## Implementation level
- Real authored files (src): 12
- Scaffold/generated files: 0 (all placeholder stubs removed)
- Broken: 0

## What is implemented (real behavior)
- `Claim` / `Evidence` / `Source` / `Provenance` / `Confidence` domain models
  with first-class uncertainty and validation.
- `KnowledgeEngine` with the full epistemic lifecycle:
  CLAIM -> EVIDENCE -> SOURCE -> PROVENANCE -> VERIFICATION
  -> CONFIDENCE + UNCERTAINTY -> KNOWLEDGE STATE.
- Knowledge states: supported, unsupported, uncertain, contradictory,
  outdated, unverified.
- Verification is explicit and distinct from confidence; unsupported claims
  never become verified knowledge.
- Contradiction detection (inter-claim and intra-claim); conflicting evidence
  stays visible and blocks verification.
- Provenance accumulation that is never silently lost.
- Freshness engine with TTL and exponential half-life decay.
- Evidence fusion that raises uncertainty on conflict instead of averaging it
  away.
- Trust model (evidence quality x source reputation x freshness x verification
  multiplier).
- Source reputation updates from verification outcomes.
- Retrieval ranked with verified-first ordering and a first-class "I do not
  know" signal (`KnowledgeResult.says_unknown`).
- Security posture: poisoned/low-reputation sources cannot promote claims to
  verified knowledge; instruction-like text is treated as plain data.
- Canonical adapter bridging to `aura.knowledge` types (id-preserving).

## Tests
- 59 passing, 1 skipped (canonical-bridge unavailable test; the bridge IS
  available in this environment so the skip is expected).
- Covers: contradictory evidence, unsupported claim, unverified/poisoned
  source, provenance preservation, stale knowledge, evidence fusion,
  confidence-vs-verification distinction, retrieval ranking, revision,
  security, trust, freshness, canonical integration, full lifecycle e2e.

## Validation gates
- Syntax compilation: PASS (ast parse over all 12 src files)
- Import validation: PASS (`from aura_knowledge import *` -> 23 exports)
- Unit + integration tests: PASS (59 passed, 1 skipped)
- Lint (ruff): PASS (exit 0)
- Type check (mypy): PASS (exit 0)
- Build/package check: NOT RUN (package not pip-installed in this session)

## Supported runtime status
- IMPORTED BY RUNTIME: No (standalone; canonical `aura/` is the runtime)
- PRODUCTION READY: IMPLEMENTED (tested core + e2e lifecycle; package
  install/build not yet exercised)

## Known limitations
- In-memory only; no durable persistence backend in this repo.
- Contradiction detection is heuristic (predicate + negation polarity).
- Canonical bridge is one-directional for evidence direction (canonical
  `Evidence` has no support direction).

