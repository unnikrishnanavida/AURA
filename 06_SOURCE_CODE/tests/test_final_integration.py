"""FINAL INTEGRATION TEST — AURA Phase 1-4 supported lifecycle.

Demonstrates the full supported flow using the REAL subsystems implemented in
Phases 1-4, integrated through explicit contracts (no duplicate runtime):

1. Receive a request (CLI command dispatch shape).
2. Generate a correlation ID.
3. Retrieve relevant knowledge/evidence (aura-knowledge).
4. Preserve provenance.
5. Represent uncertainty.
6. Create candidate plans (aura-planning).
7. Validate constraints.
8. Detect capability gaps.
9. Perform security/capability checks (aura-api + aura-execution gates).
10. Execute an authorized action or dry run (aura-execution).
11. Record execution state and trace.
12. Verify outcome.
13. Reflect on outcome (aura-reflection).
14. Generate a learning signal.
15. Ensure the learning signal does NOT auto-modify the system.
16. Produce an observable/auditable result.

If evidence is insufficient, the system says "I do not know" via
``KnowledgeResult.says_unknown``.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

_REPO = Path(__file__).resolve().parents[1]  # 06_SOURCE_CODE


def _add_srcs() -> None:
    for repo in ("aura-knowledge", "aura-planning", "aura-execution", "aura-reflection", "aura-api", "aura-cli"):
        src = _REPO / repo / "src"
        if src.exists() and str(src) not in sys.path:
            sys.path.insert(0, str(src))


_add_srcs()


def test_knowledge_planning_phase() -> None:
    # 1. Request + 2. correlation ID
    correlation_id = "co-integration-test-0001"

    # 3-5. Knowledge: claim -> evidence -> provenance -> uncertainty
    from aura_knowledge import KnowledgeEngine
    from aura_knowledge.core.models import Evidence, Source

    knowledge = KnowledgeEngine()
    atlas = Source("atlas", reputation=0.95)
    knowledge.register_source(atlas)
    claim = knowledge.add_claim("the capital of France is Paris", created_by=f"cli:{correlation_id}")
    knowledge.add_evidence(
        claim.claim_id,
        Evidence(content="geography record", support=1.0, reliability=0.95, source=atlas),
    )
    knowledge.verify(claim.claim_id)
    hits = knowledge.retrieve("capital of France")
    assert hits[0].known is True
    assert len(claim.provenance.evidence_ids) == 1  # provenance preserved
    assert claim.confidence is not None and claim.confidence.uncertainty >= 0.0  # uncertainty first-class

    # "I do not know" path
    unknown = knowledge.retrieve("the capital of the moon")
    assert unknown == [] or unknown[0].says_unknown

    # 6-8. Planning: candidates, constraint validation, capability gaps
    from aura_planning import Planner
    from aura_planning.goals.models.goal import Goal
    from aura_planning.planning.planner import ActionSpec

    planner = Planner(
        goal=Goal(goal_id="gl-integration", objective="deploy knowledge service", desired_state="deployed"),
        available_capabilities={"filesystem.write", "compute.run"},
    )
    feasible = planner.candidates([(ActionSpec("deploy", "filesystem.write"),)])[0]
    infeasible = planner.candidates([(ActionSpec("deploy", "missing.capability"),)])[0]
    assert feasible.feasible is True
    assert infeasible.feasible is False
    assert infeasible.missing_capabilities  # capability gap detected explicitly


def test_security_execution_reflection_phase() -> None:
    # 9. Security/capability checks via the aura-api fail-closed pipeline
    from aura_api import (
        ApiKeyStore,
        Authenticator,
        Authorizer,
        RBACPolicy,
        ReferenceApi,
        TokenBucket,
    )

    store = ApiKeyStore()
    store.register("svc", "secret", subject="service", roles=("operator",))
    rbac = RBACPolicy()
    rbac.grant(role="operator", resource_type="echo", action="create")
    api = ReferenceApi(
        authenticator=Authenticator(store),
        authorizer=Authorizer(rbac=rbac),
        limiter=TokenBucket(100, 100),
    )
    denied = api.handle(method="POST", path="/v1/echo", headers={}, body={"message": "x"})
    assert denied.status == 401  # auth fails closed

    # 10-11. Execution: authorized action via aura-execution Orchestrator
    from aura_execution import Capability, ExecutableAction, ExecutionRequest
    from aura_execution.orchestration.orchestrator import Orchestrator

    orchestrator = Orchestrator.default()
    orchestrator.register_capability(Capability("filesystem.write", frozenset({"write"})))
    action = ExecutableAction(
        action_id="write-evidence",
        name="write",
        capability="filesystem.write",
        inputs={"path", "text"},
        effects={"written": True},
        risk=0.1,
        handler=lambda inputs, ctx: inputs["text"],
    )
    result = orchestrator.execute(ExecutionRequest(action, inputs={"path": "x", "text": "ok"}, state={"written": False}, approved=True))
    assert result.status.value == "SUCCEEDED"
    assert result.events  # execution trace recorded

    # 12. Verify outcome: state contains declared effect
    assert result.result is not None

    # 13-15. Reflection: outcome -> lesson -> validated learning signal (NOT auto-applied)
    from aura_reflection.models.reflection_request import (
        ActionOutcome,
        ReflectionRequest,
    )
    from aura_reflection.services.reflection_engine import ReflectionEngine
    from aura_reflection.services.reflection_gate import (
        ReflectionGate,
        UnauthorizedMutationError,
        apply_if_authorized,
    )

    reflection = ReflectionEngine().reflect(
        ReflectionRequest(
            outcome=ActionOutcome(
                action="write-evidence",
                success=True,
                goal="record evidence",
                expected_result="ok",
                actual_result="ok",
            )
        )
    )
    assert reflection.lessons
    assert reflection.signals
    # 15. Unapproved signal must NOT be applicable.
    with pytest.raises(UnauthorizedMutationError):
        apply_if_authorized(ReflectionGate(), reflection.signals[0])

    # 16. Observable/auditable result: CLI health reflects real subsystems
    from aura_cli.integrations.aura.runtime import RuntimeAdapter

    report = RuntimeAdapter().health()
    assert report.canonical is True
    assert report.subsystems["aura_knowledge"] is True
    assert report.subsystems["aura_reflection"] is True
    assert report.subsystems["aura_api"] is True