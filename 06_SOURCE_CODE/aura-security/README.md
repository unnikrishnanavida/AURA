# aura-security

AURA Security subsystem: **adaptive defense** with a guarded, auditable
remediation lifecycle.

## Purpose

Detect threats, classify them deterministically, propose the smallest
remediation that closes the identified control gap, and — only after explicit
approval and a healthy canary — activate it. **The engine never deploys
remediation on its own.**

## Architecture

```
detect -> classify -> assess -> propose -> approve -> canary -> activate
                                                              -> rollback
```

- `src/aura_security/models/` — `Threat`, `ThreatAssessment`, `Remediation`,
  `RemediationPlan`, `ChangeRequest`, enums (`AttackClass`, `ThreatSeverity`,
  `RemediationKind`, `RemediationStatus`)
- `src/aura_security/analysis/` — `ControlGapAnalyzer`, `DefenseSelector`
- `src/aura_security/deployment/` — `ApprovalGate`, `CanaryDeployer`,
  `ChangeControl`, `RollbackManager`
- `src/aura_security/services/` — `AdaptiveDefenseEngine` (the orchestrator)

## Safety properties (tested)

1. Low-severity threats never produce remediation plans.
2. A missing approver (or same-as-requester) blocks activation.
3. High/critical remediation requires an approver with the `security` role.
4. An unhealthy canary never reaches activation.
5. Every lifecycle transition is recorded by `ChangeControl`.
6. Activation only occurs through injected deployer callbacks — nothing is
   applied implicitly.

## Quick start

```python
from aura_security import AdaptiveDefenseEngine, Threat

engine = AdaptiveDefenseEngine()
outcome = engine.detect(
    Threat(id="t1", kind="sql injection detected", indicators={"pattern": "SELECT * FROM users"}),
    approver="soc.admin",
    approver_roles=("security",),
    apply_canary=lambda r: 0.95,
    promote=lambda r: None,
)
print(outcome.activated)  # True only after approval + healthy canary
```

## Testing / quality

```bash
python -m pytest Tests
python -m ruff check src
python -m mypy src
```

Current status: adaptive-defense vertical slice **IMPLEMENTED and tested**
(9 tests, mypy clean, ruff clean). The remaining generated scaffold areas
(Authentication, Authorization, Zero-Trust, Privacy, Secrets, Threat-Models,
Policies, Audit, Sandbox) are documented as **INTERFACE READY** — their files
are empty "implementation pending" stubs awaiting the same treatment.
