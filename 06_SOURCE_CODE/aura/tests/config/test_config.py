"""Config tests: typed settings, layered loading, environment overrides, validation."""

from __future__ import annotations

import pytest

from aura.config.loader import ConfigLoader, load_settings, validate_environment
from aura.config.settings import AuraConfig, Environments
from aura.foundation.errors import ConfigurationError


def test_defaults() -> None:
    config = AuraConfig()
    assert config.environment is Environments.DEV
    assert config.instance_id == "default"
    assert config.budgets.max_actions == 50


def test_environment_validation() -> None:
    assert validate_environment("production") is Environments.PRODUCTION
    with pytest.raises(ConfigurationError):
        validate_environment("moonbase")


def test_loader_env_override() -> None:
    config = ConfigLoader().load(
        env={"AURA_INSTANCE_ID": "worker-1", "AURA_BUDGETS_MAX_ACTIONS": "7"}
    )
    assert config.instance_id == "worker-1"
    assert config.budgets.max_actions == 7


def test_loader_overrides() -> None:
    config = ConfigLoader().load(overrides={"environment": "research"})
    assert config.environment is Environments.RESEARCH


def test_load_settings() -> None:
    config = load_settings(
        environment="production",
        overrides={"storage": {"backend": "sqlite", "sqlite_path": ":memory:"}},
    )
    assert config.environment is Environments.PRODUCTION
    assert config.storage.backend == "sqlite"

def test_load_settings_honors_environment_variables(monkeypatch) -> None:
    """load_settings() (CLI path) must not ignore AURA_* env vars (P28-2)."""
    monkeypatch.setenv("AURA_ENVIRONMENT", "production")
    monkeypatch.setenv("AURA_STORAGE_BACKEND", "sqlite")
    config = load_settings()
    assert config.environment is Environments.PRODUCTION
    assert config.storage.backend == "sqlite"


def test_load_settings_explicit_environment_still_forces() -> None:
    """An explicitly non-default environment argument keeps forcing the value."""
    config = load_settings(
        environment="production",
        overrides={"storage": {"backend": "sqlite", "sqlite_path": ":memory:"}},
    )
    assert config.environment is Environments.PRODUCTION


def test_load_settings_defaults_to_development_without_overrides(monkeypatch) -> None:
    monkeypatch.delenv("AURA_ENVIRONMENT", raising=False)
    config = load_settings()
    assert config.environment is Environments.DEV

def test_production_rejects_in_memory_storage() -> None:
    with pytest.raises(ConfigurationError):
        load_settings(environment="production")


def test_nested_section_override() -> None:
    config = ConfigLoader().load(env={"AURA_ENGINES_REASONING_SEED": "42"})
    assert config.engines.reasoning_seed == 42


def test_invalid_numeric_rejected() -> None:
    with pytest.raises(ConfigurationError):
        ConfigLoader().load(env={"AURA_BUDGETS_MAX_ACTIONS": "not-a-number"})


def test_secret_redaction() -> None:
    config = AuraConfig(provider_api_key="super-secret-value")
    safe = config.model_dump_safe()
    assert safe["provider_api_key"] == "***REDACTED***"
    assert "super-secret-value" not in str(safe)