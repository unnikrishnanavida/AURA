# Canonical Components

Authoritative implementations in `06_SOURCE_CODE/aura/`:

1. **foundation** — ids, errors, Result, clocks, lifecycle, cancellation, RNG,
   validation, serialization.
2. **config** — typed settings + layered loader (defaults -> file -> env),
   secret redaction.
3. **core** — bootstrap, DI container, component registry, lifecycle manager,
   health/readiness.
4. **memory** — working/episodic/semantic/procedural, provenance, confidence,
   graph, consolidation, replay-to-memory.
5. **knowledge** — claims/evidence/sources, trust model, verification,
   contradiction detection.
6. **reasoning** — deductive/abductive/causal/probabilistic/counterfactual/
   analogical + consensus + verification + uncertainty-first.
7. **planning** — goal decomposition, constraints, risk analysis, comparison.
8. **execution** — action models, world-state vs action-input, idempotency,
   checkpoints.
9. **reflection** — post-execution review, counterfactual lessons.
10. **learning** — validated signal gate, versioning, rollback, auth gate.
11. **brain** — cognitive orchestration with bounded loops.
12. **security** — capabilities, default-deny permissions, safety, autonomy,
    budgets, recovery, audit, redaction, adaptive defense.
13. **observability** — logging, metrics, flight recorder, replay, provenance.
14. **providers** — provider registry + embedded provider.
15. **research** — ledger, claim passport, evidence provenance, hypotheses.
16. **sdk/api/cli** — public interfaces.

## Standalone canonical owners

- Agents: `aura-agents` engine (bridged by `aura/agents`).
- Research engine: `aura-research` (mirrored by `aura/research`).
- Security adaptive-defense: `aura-security`.
- Execution engine (complete): `aura-execution-complete`.
- Cloud: `aura-cloud`.