"""Reasoning domain tests: uncertainty-first, strategies, consensus, verification."""

from __future__ import annotations

from aura.providers.result import ProviderResult, ProviderStatus
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


def test_generation_provider_answers_unresolved_general_question() -> None:
    class GenerationManager:
        last_provider = "test-model"

        def __init__(self) -> None:
            self.request: dict[str, object] = {}

        def generate(self, **kwargs: object) -> ProviderResult:
            self.request = kwargs
            return ProviderResult(
                status=ProviderStatus.OK,
                text="Machine learning is a way for software to learn patterns from data.",
                provider="test-model",
                model="test-model-v1",
                local=False,
            )

    manager = GenerationManager()
    engine = ReasoningEngine(provider_manager=manager)
    result = engine.reason(ReasoningInput(question="What is machine learning?", facts={}))

    assert result.answer.startswith("Machine learning is")
    assert result.confidence is None
    assert result.uncertainty is None
    assert result.provider_mode == "generation"
    assert result.provider_status == "ok"
    assert result.provider_model == "test-model-v1"
    # A generated answer is explicitly NOT verified.
    assert result.provider_verified is False
    assert manager.request["question"] == "What is machine learning?"
    # The provider receives the Step 1A context as a structured handoff.
    messages = manager.request["messages"]
    assert isinstance(messages, list) and messages
    assert messages[0]["role"] == "system"
    assert "USER REQUEST" in messages[-1]["content"]


def test_unresolved_general_question_does_not_report_strategy_confidence() -> None:
    result = make_engine().reason(
        ReasoningInput(question="What is machine learning?", facts={})
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


# -- REAS-1: evidence-aware strategy selection ---------------------------------


def test_selection_core_strategies_without_context() -> None:
    engine = make_engine()
    selected = engine.select_strategies(ReasoningInput(question="q", facts={}))
    assert selected == ("deductive", "abductive", "causal", "probabilistic")


def test_selection_variety_with_context() -> None:
    engine = make_engine()
    inp = ReasoningInput(
        question="q",
        facts={},
        hypotheses=("h1",),
        cases=(Case(attrs=frozenset({"a"}), outcome="o"),),
    )
    assert engine.select_strategies(inp) == (
        "deductive",
        "abductive",
        "causal",
        "probabilistic",
        "counterfactual",
        "analogical",
    )


def test_selection_observable_on_result() -> None:
    result = make_engine().reason(
        ReasoningInput(
            question="q",
            facts={},
            hypotheses=("h1",),
        )
    )
    assert "counterfactual" in result.strategies_selected
    assert "analogical" not in result.strategies_selected
    assert "strategies" in result.to_dict()