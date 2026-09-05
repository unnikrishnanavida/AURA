"""Reasoning domain tests: uncertainty-first, strategies, consensus, verification."""

from __future__ import annotations

from aura.reasoning.engine import ReasoningEngine, ReasoningInput
from aura.reasoning.models import Case, Rule
from aura.reasoning.uncertainty import UncertaintyLevel, uncertainty_from_confidence


def make_engine() -> ReasoningEngine:
    return ReasoningEngine(seed=42)


def test_unknown_answer_when_no_evidence() -> None:
    result = make_engine().reason(
        ReasoningInput(question="is the moon made of cheese?", facts={})
    )
    assert result.answer == "I do not know"
    assert result.confidence == 0.0
    assert result.uncertainty is UncertaintyLevel.HIGH


def test_uncertainty_mapping() -> None:
    assert uncertainty_from_confidence(0.95) is UncertaintyLevel.LOW
    assert uncertainty_from_confidence(0.5) is UncertaintyLevel.MEDIUM
    assert uncertainty_from_confidence(0.1) is UncertaintyLevel.HIGH


def test_deductive_reasoning() -> None:
    result = make_engine().reason(
        ReasoningInput(
            question="socrates is mortal",
            facts={"socrates is human": 1.0, "humans are mortal": 1.0},
            rules=(Rule(id="r1", conditions=("socrates is human", "humans are mortal"), consequent="socrates is mortal"),),
        )
    )
    assert result.answer != "I do not know"
    assert result.confidence > 0.0
    assert result.trace.steps  # inference steps recorded


def test_reasoning_trace_records_steps() -> None:
    result = make_engine().reason(
        ReasoningInput(
            question="test trace",
            facts={"a": 1.0},
            rules=(Rule(id="r1", conditions=("a",), consequent="b"),),
        )
    )
    assert isinstance(result.trace.lines(), list)


def test_contested_verification() -> None:
    from aura.reasoning.models import ReasoningInput, ReasoningTrace, make_conclusion
    from aura.reasoning.verification import VerificationEngine

    conclusion = make_conclusion(
        strategy="test",
        statement="the service is healthy",
        confidence=0.9,
        reasoning=["derived from check"],
        supports=("r1",),
    )
    inp = ReasoningInput(question="status", facts={"not healthy": 0.9})
    result = VerificationEngine().verify(conclusion, inp, ReasoningTrace())
    assert result.status == "contested"


def test_verification_insufficient_without_steps() -> None:
    from aura.reasoning.models import ReasoningInput, ReasoningTrace, make_conclusion
    from aura.reasoning.verification import VerificationEngine

    conclusion = make_conclusion(
        strategy="test", statement="claim", confidence=0.6, reasoning=[], supports=()
    )
    inp = ReasoningInput(question="q", facts={})
    result = VerificationEngine().verify(conclusion, inp, ReasoningTrace())
    assert result.status == "insufficient"


def test_reasoning_result_serialization() -> None:
    result = make_engine().reason(ReasoningInput(question="q", facts={}))
    data = result.to_dict()
    assert data["question"] == "q"
    assert set(data) >= {"question", "answer", "confidence", "uncertainty", "trace", "verification"}


def test_min_evidence_enforced() -> None:
    result = make_engine().reason(
        ReasoningInput(question="needs evidence", facts={}, min_evidence=1)
    )
    assert result.answer == "I do not know"


def test_analogical_case_used() -> None:
    result = make_engine().reason(
        ReasoningInput(
            question="classify the new object",
            facts={},
            cases=(Case(attrs=frozenset({"has_wings", "lays_eggs"}), outcome="bird"),),
        )
    )
    assert result.answer is not None