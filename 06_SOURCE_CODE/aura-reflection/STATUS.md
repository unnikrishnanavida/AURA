# STATUS: aura-reflection

## Architectural role
AUTHORITATIVE reflective-intelligence subsystem (execution/reasoning review,
failure & success analysis, assumption review, counterfactual analysis,
lesson extraction, validated learning signals). Proper `src/aura_reflection`
package layout; real modules preserved from the original flat `Reflection/`
layout and re-homed.

## Canonical owner
`aura/src/aura/reflection` (canonical runtime `aura/`). This repo is a
standalone subsystem that integrates with the canonical runtime through an
explicit adapter (`aura_reflection.integrations.aura_canonical`).

## Implementation level
- Real authored files (src): 18
- Scaffold/generated files: 0 (flat stub directories removed; real modules
  preserved and relocated)
- Broken: 0

## Preserved real code
- `models/reflection_request.py` (ActionOutcome, OutcomeKind, ReflectionRequest)
- `models/reflection_result.py` (ReviewFinding, AnalysisFinding, Lesson,
  ImprovementSignal, Counterfactual, ReflectionResult)
- `services/reflection_engine.py` (deterministic bounded reflection)
- `services/reflection_gate.py` (authorization boundary; signals never
  self-approved)
- `Tests/unit/test_reflection_engine_real.py` (behavioral tests, repointed to
  the `aura_reflection` package)

## What is implemented (real behavior)
- Full reflective flow: ACTION -> OUTCOME -> REFLECTION (failure/success +
  assumption review) -> COUNTERFACTUAL ANALYSIS -> LESSON -> VALIDATED
  LEARNING SIGNAL.
- ReflectionOrchestrator composing engine + evidence gate + learning broker.
- EvidenceGate (validation boundary): insufficient evidence yields an
  explicit "I do not know" verdict instead of a fabricated lesson.
- LearningSignalBroker that packages ONLY gate-approved signals; unapproved
  signals are refused. Learning signals are redacted (no secret leakage).
- MemoryBridge that refuses to write memory without an approved learning
  signal (reflection never auto-writes memory).
- MistakeDetector (unverified assumption, missing precondition, no observable
  outcome) and StrategyEvaluator (appropriate / suboptimal) analysis modules.
- Canonical adapter translating to/from `aura.reflection` contracts.

## Tests
- 36 passing, 1 skipped (canonical-bridge-unavailable test; bridge IS
  available here so skip is expected).
- Covers: failed execution, incorrect assumption, poor strategy, successful
  outcome, counterfactual comparison, invalid learning signal, unauthorized
  automatic modification rejection, secret redaction, evidence gate, full
  lifecycle e2e, canonical adaptation.

## Validation gates
- Syntax compilation: PASS (ast parse over all 18 src files)
- Import validation: PASS (`from aura_reflection import *` -> 19 exports)
- Unit + integration tests: PASS (36 passed, 1 skipped)
- Lint (ruff): PASS (exit 0)
- Type check (mypy): PASS (exit 0)
- Build/package check: NOT RUN (package not pip-installed in this session)

## Supported runtime status
- IMPORTED BY RUNTIME: No (standalone; canonical `aura/` is the runtime)
- PRODUCTION READY: IMPLEMENTED (tested core + gate + e2e lifecycle; package
  install/build not yet exercised)

## Known limitations
- Reflection analyzes a single episode; cross-episode trend analysis is not
  implemented.
- Counterfactuals are heuristic (no plan simulation).
- Canonical adapter maps one direction of evidence; not a full bidirectional
  model.
