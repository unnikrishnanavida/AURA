"""Phase 29: reasoning consulting the provider boundary for safe synthesis."""

from __future__ import annotations

from aura.observability.metrics import Metrics
from aura.providers.base import Provider, ProviderProfile
from aura.providers.errors import ProviderError
from aura.providers.manager import ProviderManager
from aura.reasoning.engine import ReasoningEngine, ReasoningInput
from aura.reasoning.models import Rule


class RecordingProvider(Provider):
    def __init__(self, *, result: str = "provider-synthesized", error: Exception | None = None) -> None:
        self.name = "recorder"
        self.timeout_seconds = 5.0
        self._result = result
        self._error = error
        self.calls = 0
        self.context: dict[str, object] = {}
        self.profile = ProviderProfile(
            name="recorder", kind="reasoning", capabilities=("reasoning.synthesis",), privacy_approved=True
        )

    def health(self) -> bool:
        return True

    def reason(self, question: str, **kwargs: object) -> object:
        self.calls += 1
        self.context.update(kwargs)
        if self._error is not None:
            raise self._error
        return self._result


def _manager(fake: Provider) -> ProviderManager:
    manager = ProviderManager(metrics=Metrics())
    manager.register(fake)
    return manager


def _evidence_input() -> ReasoningInput:
    return ReasoningInput(
        question="socrates is mortal",
        facts={"socrates is human": 1.0, "humans are mortal": 1.0},
        rules=(
            Rule(id="r1", conditions=("socrates is human", "humans are mortal"), consequent="socrates is mortal"),
        ),
    )


def test_reasoning_consults_provider_for_synthesis() -> None:
    fake = RecordingProvider()
    engine = ReasoningEngine(seed=42, provider_manager=_manager(fake))
    result = engine.reason(_evidence_input())
    assert fake.calls == 1
    assert result.answer == "provider-synthesized"
    assert result.provider_name == "recorder"
    assert result.provider_synthesized is True
    data = result.to_dict()
    assert data["provider"] == {"name": "recorder", "synthesized": True}
    assert fake.context["context"]["question"] == "socrates is mortal"
    assert "conclusions" in fake.context["context"]


def test_deterministic_path_without_manager_is_unchanged() -> None:
    engine = ReasoningEngine(seed=42)
    result = engine.reason(_evidence_input())
    assert result.answer != "I do not know"
    assert result.provider_name is None
    assert result.provider_synthesized is False
    assert "provider" not in result.to_dict()


def test_uncertainty_first_outcomes_are_not_overridden() -> None:
    fake = RecordingProvider()
    engine = ReasoningEngine(seed=42, provider_manager=_manager(fake))
    result = engine.reason(ReasoningInput(question="no evidence", facts={}))
    assert result.answer == "I do not know"
    assert fake.calls == 0  # provider was never consulted
    assert result.provider_synthesized is False


def test_provider_failure_falls_back_to_deterministic_answer() -> None:
    metrics = Metrics()
    fake = RecordingProvider(error=ProviderError("down"))
    manager = ProviderManager(metrics=metrics)
    manager.register(fake)
    engine = ReasoningEngine(seed=42, provider_manager=manager)
    result = engine.reason(_evidence_input())
    assert result.answer != "I do not know"  # deterministic fallback returned
    assert result.provider_synthesized is False
    assert metrics.count("provider_failure") == 1


def test_brain_passes_provider_boundary_end_to_end() -> None:
    from aura.brain.engine import BrainEngine
    from aura.config.settings import AuraConfig

    metrics = Metrics()
    fake = RecordingProvider()
    manager = ProviderManager(metrics=metrics)
    manager.register(fake)
    brain = BrainEngine.create(config=AuraConfig(), seed=42, provider_manager=manager)
    result = brain.reason(
        question="socrates is mortal",
        facts={"socrates is human": 1.0, "humans are mortal": 1.0},
        rules=(Rule(id="r1", conditions=("socrates is human", "humans are mortal"), consequent="socrates is mortal"),),
    )
    assert result.reasoning is not None
    assert result.reasoning.answer == "provider-synthesized"
    assert result.reasoning.provider_name == "recorder"
    assert metrics.count("provider_call") == 1
    assert brain.provider_manager is manager


def test_multi_strategy_provider_not_used_for_synthesis() -> None:
    """Embedded-style providers never satisfy the synthesis capability (no recursion)."""
    from aura.providers.embedded import EmbeddedReasoningProvider

    manager = ProviderManager()
    manager.register(EmbeddedReasoningProvider(seed=1))
    assert manager.select(required_capability="reasoning.multi_strategy") == ["embedded"]
    assert manager.select(required_capability="reasoning.synthesis") == []
    engine = ReasoningEngine(seed=42, provider_manager=manager)
    result = engine.reason(_evidence_input())
    assert result.answer != "I do not know"
    assert result.provider_synthesized is False