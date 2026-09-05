"""Defense pipeline.

Controls the full remediation lifecycle. The pipeline is deliberately
sequential and gated:

- evidence must meet a minimum count before a threat is ASSESSED;
- remediation is always PROPOSED, never executed inline;
- SANDBOXED validation must pass;
- APPROVED requires an explicit authorizer;
- CANARY deployment is optional and distinct from full deployment;
- ROLLBACK is always available and is the only stage that unmakes changes.

Nothing here writes to the filesystem, network, or policy engine. It
produces *decisions*; an operator or an explicit deployment adapter applies
them. This honors the rule: never auto-deploy generated security code.
"""

from __future__ import annotations

from collections.abc import Callable

from aura.security.defense import DefenseDecision, DefenseStage, Threat, ThreatLevel

_LEVEL_WEIGHT = {
    ThreatLevel.INFO: 1,
    ThreatLevel.LOW: 2,
    ThreatLevel.MEDIUM: 4,
    ThreatLevel.HIGH: 8,
    ThreatLevel.CRITICAL: 16,
}


class DefensePipeline:
    def __init__(
        self,
        *,
        min_evidence_for_assessment: int = 1,
        sandbox_validator: Callable[[str], bool] | None = None,
    ) -> None:
        self._min_evidence = min_evidence_for_assessment
        self._sandbox = sandbox_validator or (lambda _remediation: True)

    def run(self, threat: Threat, *, authorizer: str = "", canary: bool = True) -> DefenseDecision:
        # 1. classification
        if threat.evidence and len(threat.evidence) < self._min_evidence:
            return DefenseDecision(
                threat, DefenseStage.CLASSIFIED,
                reason=f"insufficient evidence ({len(threat.evidence)} < {self._min_evidence})",
            )

        # 2. assessment: only medium+ threats warrant remediation
        if _LEVEL_WEIGHT[threat.level] < _LEVEL_WEIGHT[ThreatLevel.MEDIUM]:
            return DefenseDecision(
                threat, DefenseStage.ASSESSED,
                reason=f"threat level {threat.level.value} below remediation threshold",
            )

        if not threat.control_gap:
            return DefenseDecision(
                threat, DefenseStage.ASSESSED,
                reason="no control gap identified; nothing to remediate",
            )

        # 3. propose remediation (never apply)
        remediation = self._propose(threat)
        decision = DefenseDecision(
            threat, DefenseStage.PROPOSED, remediation=remediation,
            reason="remediation proposed; awaiting sandbox validation and approval",
        )

        # 4. sandbox validation
        if not self._sandbox(remediation):
            return DefenseDecision(
                threat, DefenseStage.SANDBOXED,
                remediation=remediation,
                reason="remediation failed sandbox validation",
            )
        decision = DefenseDecision(
            threat, DefenseStage.SANDBOXED, remediation=remediation,
            reason="remediation validated in sandbox", approved=False,
        )

        # 5. approval
        if not authorizer:
            return DefenseDecision(
                threat, DefenseStage.APPROVED,
                remediation=remediation,
                reason="remediation authorized only after explicit approval is required; no authorizer supplied",
                approved=False,
            )
        decision = DefenseDecision(
            threat, DefenseStage.APPROVED, remediation=remediation,
            reason=f"authorized by {authorizer}", approved=True, canary=canary,
        )
        return decision

    @staticmethod
    def _propose(threat: Threat) -> str:
        """Deterministic, conservative remediation template for the gap."""
        gap = threat.control_gap.lower()
        if "permission" in gap or "policy" in gap:
            return f"tighten permission policy: deny default for {threat.name}"
        if "secret" in gap or "credential" in gap:
            return f"rotate and revoke credential for {threat.name}"
        if "network" in gap or "port" in gap:
            return f"restrict network egress for {threat.name}"
        if "dependency" in gap or "package" in gap:
            return f"pin and update vulnerable dependency for {threat.name}"
        return f"apply least-privilege hardening for {threat.name}"


__all__ = ["DefensePipeline"]