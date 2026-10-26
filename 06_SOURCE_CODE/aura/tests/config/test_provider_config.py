"""Provider configuration validation (Phase 39, WORKSTREAM A4).

Deterministic, offline tests for malformed provider configuration and for the
guard that a partially-configured remote provider is never silently
constructed. Live provider calls are NOT attempted here.
"""

from __future__ import annotations

import pytest

from aura.config.settings import AuraConfig, ProviderConfig
from aura.providers.manager import build_provider_manager


def test_provider_config_accepts_supported_kinds() -> None:
    for kind in ("openai", "ollama"):
        cfg = ProviderConfig(enabled=True, kind=kind, base_url="http://127.0.0.1:1/", model="m")
        assert cfg.kind == kind


def test_provider_config_rejects_unknown_kind() -> None:
    with pytest.raises(ValueError):
        ProviderConfig(enabled=True, kind="anthropic")


def test_provider_config_rejects_nonpositive_timeout() -> None:
    with pytest.raises(ValueError):
        ProviderConfig(timeout_seconds=0.0)
    with pytest.raises(ValueError):
        ProviderConfig(timeout_seconds=-1.0)


def test_provider_config_defaults_disabled_and_secret_free() -> None:
    cfg = ProviderConfig()
    assert cfg.enabled is False
    assert cfg.api_key is None
    dumped = AuraConfig(provider=cfg, provider_api_key="k").model_dump_safe()
    assert dumped["provider_api_key"] == "***REDACTED***"
    assert dumped["provider"]["api_key"] is None  # absent, not a leaked value


def test_provider_config_secret_redacted_when_present() -> None:
    cfg = ProviderConfig(api_key="super-secret-value")
    dumped = AuraConfig(provider=cfg).model_dump_safe()
    assert dumped["provider"]["api_key"] == "***REDACTED***"


def test_incomplete_remote_config_never_constructs_remote() -> None:
    """enabled=True without base_url/model must NOT create a half-configured adapter."""
    cfg = AuraConfig(
        provider=ProviderConfig(enabled=True, kind="openai", name="sketch", model="", base_url="")
    )
    manager = build_provider_manager(cfg)
    assert manager is not None
    names = manager.registry.names()
    assert "sketch" not in names, "partial remote config must not register a provider"
    assert "embedded" in names
    assert manager.registry.default == "embedded"


def test_complete_config_constructs_remote_without_calling_it() -> None:
    cfg = AuraConfig(
        provider=ProviderConfig(
            enabled=True,
            kind="ollama",
            name="local-ollama",
            base_url="http://127.0.0.1:11434",
            model="nomic-embed",
            privacy_approved=True,
        )
    )
    manager = build_provider_manager(cfg)
    assert manager is not None
    assert manager.registry.default == "local-ollama"
    assert "local-ollama" in manager.registry.names()
    # Constructing must not perform network I/O: health probes require a call,
    # and we have not called anything.
    assert manager.usage.calls == 0 and manager.usage.failures == 0