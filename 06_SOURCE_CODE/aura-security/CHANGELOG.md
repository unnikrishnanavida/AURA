# Changelog

## [0.1.0] — 2026

Adaptive Defense vertical slice:

- **Threat assessment** — deterministic classification (`ThreatClassifier`),
  severity scoring, evidence-based confidence.
- **Control gap analysis** — maps attack classes to the security control that
  should have stopped them.
- **Defense selection** — deterministic, conservative remediation proposals.
- **Approval gate** — no remediation activates without explicit, role-checked
  approval (approver distinct from requester; `security` role for high/critical).
- **Canary deployment** — health-gated promotion; failures never reach
  activation.
- **Change control + rollback** — every lifecycle transition is audited and
  reversible.
- **AdaptiveDefenseEngine** — orchestrates the full lifecycle with injected
  deployer callbacks (production writes are never implicit).
- Tests: 9 unit tests covering classification, low-severity short-circuit,
  approval requirements, canary health, change-control audit, and the strict
  sandbox gate.

Quality: `pytest` green, `mypy` clean (14 source files), `ruff` clean.
