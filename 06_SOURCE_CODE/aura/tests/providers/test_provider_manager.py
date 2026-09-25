"""Provider manager tests: selection, policy, dispatch, failure, observability."""

from __future__ import annotations

from aura.observability.metrics import Metrics
from aura.providers.base import Provider, ProviderPolicy, ProviderProfile
from aura.providers.errors import ProviderError, ProviderTimeoutError
from aura.providers.manager import ProviderManager, build_provider_manager
from aura.security.audit import AuditLog


class FakeProvider(Provider):
    def __init__(
        self,
        name: str = "fake",
        *,
        result: str = "synthesized answer",
        error: Exception | None = None,
        health: bool = True,
        privacy_approved: bool = True,
        capability: str = "reasoning.synthesis",
    ) -> None:
        self.name = name
        self.timeout_seconds = 5.0
        self._result = result
        self._error = error
        self._health = health
        self.calls = 0
        self.last_kwargs: dict[str, object] = {}
        self.profile = ProviderProfile(
            name=name, kind="reasoning", capabilities=(capability,), privacy_approved=privacy_approved
        )

    def health(self) -> bool:
        return self._health

    def reason(self, question: str, **kwargs: object) -> object:
        self.calls += 1
        self.last_kwargs = kwargs
        if self._error is not None:
            raise self._error
        return self._result


def _manager(policy: ProviderPolicy | None = None) -> tuple[ProviderManager, Metrics, AuditLog]:
    metrics = Metrics()
    audit = AuditLog()
    manager = ProviderManager(metrics=metrics, audit=audit, policy=policy)
    return manager, metrics, audit


def test_synthesize_success_path() -> None:
    manager, metrics, audit = _manager()
    fake = FakeProvider()
    manager.register(fake)
    result = manager.synthesize(question="q", conclusions=[], verification={})
    assert result == "synthesized answer"
    assert manager.last_provider == "fake"
    assert fake.calls == 1
    assert fake.last_kwargs["context"]["question"] == "q"
    assert manager.usage.calls == 1
    assert manager.usage.failures == 0
    assert metrics.count("provider_call") == 1
    assert metrics.count("provider_failure") == 0
    assert len(audit.entries()) == 0


def test_synthesize_none_when_no_synthesis_provider() -> None:
    manager, _, _ = _manager()
    # Embedded-style provider without the synthesis capability.
    manager.register(FakeProvider(name="embedded_only", capability="reasoning.multi_strategy"))
    assert manager.synthesize(question="q", conclusions=[], verification={}) is None
    assert manager.usage.calls == 0


def test_synthesize_provider_error_emits_failure_and_falls_back() -> None:
    manager, metrics, audit = _manager()
    manager.register(FakeProvider(error=ProviderError("boom")))
    assert manager.synthesize(question="q", conclusions=[], verification={}) is None
    assert manager.usage.calls == 0
    assert manager.usage.failures == 1
    assert metrics.count("provider_failure") == 1
    actions = [r.action for r in audit.entries()]
    assert any("provider" in a for a in actions)


def test_synthesize_timeout_is_recorded() -> None:
    manager, metrics, audit = _manager()
    manager.register(FakeProvider(error=ProviderTimeoutError("slow")))
    assert manager.synthesize(question="q", conclusions=[], verification={}) is None
    assert manager.usage.timeouts == 1
    assert metrics.count("provider_failure") == 1
    assert len(audit.entries()) == 1


def test_privacy_policy_excludes_unapproved_providers() -> None:
    manager, _, _ = _manager()  # default policy requires privacy approval
    manager.register(FakeProvider(name="remote", privacy_approved=False))
    assert manager.select() == []
    assert manager.synthesize(question="q", conclusions=[], verification={}) is None
    assert manager.usage.policy_rejections >= 1

    permissive = ProviderManager(policy=ProviderPolicy(require_privacy_approved=False))
    permissive.register(FakeProvider(name="remote", privacy_approved=False))
    assert permissive.select() == ["remote"]


def test_health_aggregation() -> None:
    manager, _, _ = _manager()
    manager.register(FakeProvider(name="ok", health=True))
    manager.register(FakeProvider(name="down", health=False))
    assert manager.health() == {"ok": True, "down": False}
    assert manager.all_healthy() is False


def test_build_provider_manager_disabled_returns_none() -> None:
    from aura.config.settings import AuraConfig

    assert build_provider_manager(AuraConfig()) is None


def test_build_provider_manager_enabled_constructs_remote() -> None:
    from aura.config.settings import AuraConfig, ProviderConfig, SecretStr

    # Remote without privacy approval -> registered but excluded by default policy.
    cfg = AuraConfig(provider=ProviderConfig(enabled=True, base_url="http://example.invalid", model="m"))
    manager = build_provider_manager(cfg)
    assert manager is not None
    assert manager.select(required_capability="reasoning.multi_strategy") == ["embedded"]
    assert manager.select(required_capability="reasoning.synthesis") == []

    # Privacy-approved remote -> selectable for synthesis.
    cfg2 = AuraConfig(
        provider=ProviderConfig(
            enabled=True, base_url="http://example.invalid", model="m", privacy_approved=True
        )
    )
    manager2 = build_provider_manager(cfg2)
    assert manager2 is not None
    assert manager2.select(required_capability="reasoning.synthesis") == ["default"]

    # API key is never exposed in safe dumps.
    cfg3 = AuraConfig(
        provider=ProviderConfig(
            enabled=True, base_url="http://example.invalid", model="m",
            api_key=SecretStr("sk-test-secret"),
        )
    )
    assert cfg3.provider is not None and cfg3.provider.api_key is not None
    assert "sk-test-secret" not in str(cfg3.model_dump_safe())