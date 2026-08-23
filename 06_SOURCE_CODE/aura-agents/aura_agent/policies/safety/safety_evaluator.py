"""Safety evaluator: the single, non-bypassable safety authority.

Safety is evaluated *before* autonomy and *before* dispatch. Autonomy mode can
relax *approval* gates but can never convert a ``DENY`` into an ``ALLOW``.
"""

from __future__ import annotations

from aura_agent.policies.safety.safety_decision import (
    SafetyDecision,
    SafetyDecisionValue,
    SafetyPolicy,
    SafetyRequest,
)

__all__ = ["SafetyEvaluator"]


class SafetyEvaluator:
    """Evaluates actions against safety policies.

    Rules:
    - any forbidden capability -> ``DENY`` (autonomy cannot override),
    - risk above the applicable policy's ``max_risk_score`` -> ``DENY``,
    - capability in the review set -> ``REVIEW`` (approval required even in
      autonomous mode),
    - otherwise ``ALLOW``.
    """

    def __init__(self, review_uncovered_risk: float = 0.5) -> None:
        self._policies: list[SafetyPolicy] = []
        # risk above this for a capability covered by NO policy -> REVIEW
        # (unconfident evaluation), never a silent allow or a silent deny
        self._review_uncovered = review_uncovered_risk

    def add_policy(self, policy: SafetyPolicy) -> None:
        self._policies.append(policy)

    def evaluate(self, request: SafetyRequest) -> SafetyDecision:
        reasons: list[str] = []
        violated: list[str] = []

        # 1. forbidden capabilities -> DENY (autonomy can never override)
        for policy in self._policies:
            if policy.forbids_capability(request.capability):
                reasons.append(
                    f"policy {policy.name!r} forbids capability {request.capability!r}"
                )
                violated.append(policy.name)

        if violated:
            return SafetyDecision(
                decision=SafetyDecisionValue.DENY,
                risk_score=request.risk_score,
                reasons=reasons,
                violated_policies=violated,
                evaluated_action=request.action_name,
            )

        # 2. explicit coverage -> apply the declared risk ceiling
        covering = [
            p for p in self._policies if p.covers_capability(request.capability)
        ]
        if covering:
            ceiling = min(
                p.max_risk_score for p in covering if p.max_risk_score < float("inf")
            )
            # if every covering policy left the ceiling infinite, cap at 1.0
            if ceiling == float("inf"):
                ceiling = 1.0
            if request.risk_score > ceiling:
                return SafetyDecision(
                    decision=SafetyDecisionValue.DENY,
                    risk_score=request.risk_score,
                    reasons=[
                        f"risk {request.risk_score:g} exceeds policy ceiling "
                        f"{ceiling:g} for capability {request.capability!r}"
                    ],
                    violated_policies=[p.name for p in covering],
                    evaluated_action=request.action_name,
                )

        # 3. review requirement -> REVIEW
        review_required = any(
            p.requires_review(request.capability) for p in self._policies
        )
        if review_required:
            return SafetyDecision(
                decision=SafetyDecisionValue.REVIEW,
                risk_score=request.risk_score,
                reasons=[
                    f"capability {request.capability!r} requires safety review"
                ],
                required_approval=True,
                evaluated_action=request.action_name,
            )

        # 4. unconfident evaluation: no policy covers, medium+ risk -> REVIEW
        if not covering and request.risk_score >= self._review_uncovered:
            return SafetyDecision(
                decision=SafetyDecisionValue.REVIEW,
                risk_score=request.risk_score,
                reasons=[
                    f"unconfident evaluation for capability {request.capability!r} "
                    f"at risk {request.risk_score:g}; requiring review"
                ],
                required_approval=True,
                evaluated_action=request.action_name,
            )

        return SafetyDecision(
            decision=SafetyDecisionValue.ALLOW,
            risk_score=request.risk_score,
            reasons=[
                f"approved under {len(covering)} covering safety policy"
            ],
            evaluated_action=request.action_name,
        )
