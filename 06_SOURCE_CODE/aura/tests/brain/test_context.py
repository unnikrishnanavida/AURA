"""Context contract tests.

These cover the intelligence loop that used to be missing: a stored memory or a
knowledge claim must actually reach the answer, stay attributable, respect
budgets and permissions, and never let AURA assert more than it retrieved
(sections 29 scenarios 1-3, 9 and 10).
"""

from __future__ import annotations

from aura.brain.context import ContextAssembler, ContextBudget
from aura.brain.engine import BrainEngine
from aura.foundation.clock import ManualClock
from aura.knowledge.models import Claim, Evidence, Source
from aura.memory.models import MemoryConfidence, MemoryType, Sensitivity

#: What a user who explicitly told AURA something implies: a confident,
#: deliberately-stated record. AURA still ranks and gates it.
STATED = MemoryConfidence(fact=0.9, source=0.9, freshness=0.9, relevance=0.9)
#: A hedged, weakly-sourced record must never speak for AURA on its own.
HEDGED = MemoryConfidence(fact=0.2, source=0.2, freshness=0.2, relevance=0.2)


def make_brain() -> BrainEngine:
    return BrainEngine.create(clock=ManualClock(0), seed=7)


def remember(
    brain: BrainEngine,
    text: str,
    *,
    confidence: MemoryConfidence = STATED,
    **kwargs: object,
) -> None:
    brain.memory.remember(
        key=f"ctx:{text[:24]}",
        kind=MemoryType.SEMANTIC,
        content={"text": text},
        importance=float(kwargs.pop("importance", 0.9)),
        confidence=confidence,
        **kwargs,  # type: ignore[arg-type]
    )


def add_claim(brain: BrainEngine, statement: str, predicate: tuple[str, ...]) -> Claim:
    claim = Claim.create(statement=statement, predicate=predicate)
    for index in range(2):
        claim.with_evidence(
            Evidence(
                content=f"evidence {index}",
                source=Source(id=f"s{index}", reliability=0.95),
                quality=0.95,
            )
        )
    brain.knowledge.add(claim)
    brain.knowledge.verify(claim.id)
    return claim


# -- scenario 1: memory is actually used ------------------------------------


def test_relevant_memory_reaches_the_answer() -> None:
    brain = make_brain()
    remember(brain, "the deployment window opens on Tuesday", importance=0.9)

    result = brain.reason(question="when does the deployment window open?")

    assert result.reasoning is not None
    assert result.reasoning.answer != "I do not know"
    assert result.reasoning.grounded is True
    assert "deployment window" in result.reasoning.answer
    assert result.reasoning.confidence is not None and result.reasoning.confidence > 0.0


def test_grounded_answer_is_attributable() -> None:
    brain = make_brain()
    entry = brain.memory.remember(
        key="ctx:deadline",
        kind=MemoryType.SEMANTIC,
        content={"text": "the release deadline is next friday"},
        importance=0.9,
        confidence=STATED,
    )

    summary = brain.reason(question="tell me about the release deadline").summary()

    assert summary["grounded"] is True
    context = summary["context"]
    assert context["items"][0]["reference"] == str(entry.id)
    assert context["items"][0]["source"] == "memory"
    assert context["items"][0]["provenance"]["key"] == "ctx:deadline"


def test_low_confidence_memory_does_not_ground_an_answer() -> None:
    brain = make_brain()
    remember(
        brain,
        "the deployment window opens on Tuesday",
        confidence=HEDGED,
    )

    result = brain.reason(question="when does the deployment window open?")

    assert result.reasoning is not None
    assert result.reasoning.answer == "I do not know"
    assert result.reasoning.grounded is False
    # The record is still visible and attributed -- just not strong enough.
    assert result.context is not None
    assert len(result.context.items) == 1


def test_context_is_recorded_on_the_flight_recorder() -> None:
    brain = make_brain()
    remember(brain, "the deployment window opens on Tuesday", importance=0.9)

    result = brain.reason(question="when does the deployment window open?")
    events = brain.recorder.events(execution_id=result.execution_id)

    retrieved = [event for event in events if event.event_type == "context.retrieved"]
    assert retrieved, "context assembly must be observable"
    assert retrieved[0].payload["items"] >= 1


# -- scenario 10: honest abstention -----------------------------------------


def test_unrelated_memory_never_grounds_an_answer() -> None:
    brain = make_brain()
    remember(brain, "the deployment window opens on Tuesday", importance=0.9)

    result = brain.reason(question="explain quantum chromodynamics")

    assert result.reasoning is not None
    assert result.reasoning.answer == "I do not know"
    assert result.reasoning.grounded is False
    assert result.reasoning.confidence == 0.0


def test_no_provider_and_no_context_still_abstains() -> None:
    brain = make_brain()
    result = brain.reason(question="what is the airspeed velocity of an unladen swallow")
    assert result.reasoning is not None
    assert result.reasoning.answer == "I do not know"


def test_empty_context_is_reported_as_empty() -> None:
    brain = make_brain()
    result = brain.reason(question="what is the airspeed velocity of an unladen swallow")
    context = result.summary()["context"]
    assert context["items"] == []
    assert context["dropped"] == 0
    assert context["truncated"] is False


# -- scenario 2: knowledge reaches the answer -------------------------------


def test_verified_knowledge_claim_reaches_the_answer() -> None:
    brain = make_brain()
    claim = add_claim(brain, "the production cluster runs in the frankfurt region", ("cluster",))

    result = brain.reason(question="where does the production cluster run?")

    assert result.reasoning is not None
    assert result.reasoning.grounded is True
    assert "frankfurt" in result.reasoning.answer
    assert result.context is not None
    assert result.context.items[0].reference == str(claim.id)
    assert result.context.items[0].verified is True


# -- scenario 3: contradictions are surfaced, not resolved -----------------


def test_contradictory_claims_are_surfaced_as_contested() -> None:
    brain = make_brain()
    add_claim(brain, "the production cluster runs in the frankfurt region", ("cluster",))
    add_claim(brain, "the production cluster does not run in the frankfurt region", ("cluster",))

    result = brain.reason(question="where does the production cluster run?")

    assert result.context is not None
    assert result.context.contradictions, "the conflict must be preserved in context"
    assert result.reasoning is not None
    assert result.reasoning.answer.startswith("CONTESTED:")
    assert result.reasoning.confidence == 0.0
    assert result.reasoning.grounded is True


def test_contradictions_are_reported_even_when_unrelated() -> None:
    brain = make_brain()
    add_claim(brain, "the budget is approved", ("budget",))
    add_claim(brain, "the budget is not approved", ("budget",))

    result = brain.reason(question="unrelated question about the weather")

    assert result.context is not None
    assert len(result.context.contradictions) == 1


# -- budgets and permissions -----------------------------------------------


def test_context_budget_bounds_items_and_counts_drops() -> None:
    brain = make_brain()
    for index in range(6):
        remember(brain, f"deployment note number {index} about the release", importance=0.9)

    assembler = ContextAssembler(
        memory=brain.memory,
        knowledge=brain.knowledge,
        budget=ContextBudget(max_items=2),
    )
    grounding = assembler.assemble("deployment note about the release")

    assert len(grounding.items) == 2
    assert grounding.dropped >= 1
    assert grounding.truncated is True


def test_character_budget_is_enforced() -> None:
    brain = make_brain()
    remember(brain, "deployment " * 40 + "window", importance=0.9)

    assembler = ContextAssembler(
        memory=brain.memory,
        knowledge=brain.knowledge,
        budget=ContextBudget(max_characters=50),
    )
    grounding = assembler.assemble("deployment window")

    assert grounding.items == ()


def test_restricted_memory_requires_clearance() -> None:
    brain = make_brain()
    remember(
        brain,
        "the deployment window opens on Tuesday",
        importance=0.9,
        sensitivity=Sensitivity.RESTRICTED,
    )

    denied = ContextAssembler(
        memory=brain.memory,
        knowledge=brain.knowledge,
        budget=ContextBudget(clearance=1),
    ).assemble("when does the deployment window open?")
    assert denied.items == ()
    assert denied.filtered >= 1

    allowed = ContextAssembler(
        memory=brain.memory,
        knowledge=brain.knowledge,
        budget=ContextBudget(clearance=3),
    ).assemble("when does the deployment window open?")
    assert len(allowed.items) == 1


def test_working_memory_is_not_treated_as_evidence() -> None:
    brain = make_brain()
    brain.memory.remember(
        key="ctx:working",
        kind=MemoryType.WORKING,
        content={"text": "the deployment window opens on Tuesday"},
    )

    grounding = ContextAssembler(
        memory=brain.memory,
        knowledge=brain.knowledge,
    ).assemble("when does the deployment window open?")

    assert grounding.items == ()
    assert grounding.filtered >= 1


def test_scope_isolation_is_preserved() -> None:
    brain = make_brain()
    brain.memory.remember(
        key="ctx:scoped",
        kind=MemoryType.SEMANTIC,
        content={"text": "the deployment window opens on Tuesday"},
        scope="owner:one",
    )

    grounding = ContextAssembler(
        memory=brain.memory,
        knowledge=brain.knowledge,
    ).assemble("when does the deployment window open?", scope="owner:two")

    assert grounding.items == ()


def test_history_is_counted_but_not_promoted_to_evidence() -> None:
    brain = make_brain()
    grounding = ContextAssembler(
        memory=brain.memory,
        knowledge=brain.knowledge,
    ).assemble(
        "what is the deployment window",
        history=({"role": "user", "content": "the deployment window opens on Tuesday"},),
    )

    assert grounding.turns == 1
    assert grounding.items == ()


# -- conversation routes must stay ahead of retrieval ----------------------


def test_conversation_route_still_short_circuits() -> None:
    brain = make_brain()
    result = brain.reason(question="hello")
    assert result.direct_route == "conversation"
    assert result.context is None


def test_memory_command_still_short_circuits() -> None:
    brain = make_brain()
    result = brain.reason(question="remember that the deployment window opens on Tuesday")
    assert result.direct_route == "memory"
    assert result.direct_answer is not None
def test_refuted_knowledge_is_never_used() -> None:
    from aura.knowledge.models import VerificationStatus

    brain = make_brain()
    claim = add_claim(brain, "the production cluster runs in the frankfurt region", ("cluster",))
    claim.status = VerificationStatus.REFUTED

    result = brain.reason(question="where does the production cluster run?")

    assert result.reasoning is not None
    assert result.reasoning.grounded is False


# -- Phase 2C: knowledge owner isolation is enforced in the context path -----


def test_knowledge_scope_isolation_is_enforced_in_context() -> None:
    brain = make_brain()
    claim = Claim.create(
        statement="the deployment window opens on Tuesday", predicate=("deployment",)
    )
    brain.knowledge.add(claim, owner="owner:one")

    assembler = ContextAssembler(memory=brain.memory, knowledge=brain.knowledge)

    # A different owner must not see the private claim, even though the
    # statement matches the question exactly.
    denied = assembler.assemble("when does the deployment window open?", scope="owner:two")
    assert not any(item.reference == str(claim.id) for item in denied.items)

    # The owning scope gets it, with its scope recorded on the item.
    allowed = assembler.assemble("when does the deployment window open?", scope="owner:one")
    hit = next((i for i in allowed.items if i.source == "knowledge"), None)
    assert hit is not None, "owning scope must receive its private claim"
    assert hit.reference == str(claim.id)
    assert hit.scope == "owner:one"
    assert hit.provenance["source"] == claim.provenance.source


def test_shared_knowledge_is_visible_to_every_scope() -> None:
    brain = make_brain()
    claim = Claim.create(
        statement="the deployment window opens on Tuesday", predicate=("deployment",)
    )
    brain.knowledge.add(claim)  # no owner: shared/global claim

    assembler = ContextAssembler(memory=brain.memory, knowledge=brain.knowledge)
    grounding = assembler.assemble("when does the deployment window open?", scope="owner:two")
    assert any(item.reference == str(claim.id) for item in grounding.items)


# -- Phase 2C: note-keyed memory must pass the relevance gate ----------------


def test_note_keyed_memory_passes_the_relevance_gate() -> None:
    brain = make_brain()
    entry = brain.memory.remember(
        key="ctx:note",
        kind=MemoryType.SEMANTIC,
        content={"note": "the deployment window opens on Tuesday"},
        importance=0.9,
        confidence=STATED,
    )

    grounding = ContextAssembler(
        memory=brain.memory, knowledge=brain.knowledge
    ).assemble("when does the deployment window open?")

    assert any(item.source == "memory" and item.reference == str(entry.id) for item in grounding.items)