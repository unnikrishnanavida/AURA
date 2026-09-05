"""Typed configuration models.

Configuration is the single source of runtime truth for every engine. The
module declares the schema version explicitly so persisted payloads can be
migration-checked.
"""

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, Field, SecretStr, field_validator, model_validator


class Environments(StrEnum):
    DEV = "development"
    TEST = "testing"
    RESEARCH = "research"
    STAGING = "staging"
    PRODUCTION = "production"


class ConfigSchemaVersion(StrEnum):
    V1 = "v1"


class BudgetLimits(BaseModel):
    """Multi-dimensional execution budgets shared by agents and tools."""

    max_actions: int = Field(default=50, ge=1)
    max_seconds: float = Field(default=120.0, gt=0)
    max_cost: float = Field(default=10.0, ge=0)
    max_tokens: int = Field(default=200_000, ge=1)


class LoggingConfig(BaseModel):
    level: str = Field(default="INFO")
    json_format: bool = Field(default=True)
    redact_secrets: bool = Field(default=True)


class EngineConfig(BaseModel):
    """Per-engine toggles. Engines default to conservative, deterministic behavior."""

    memory_enabled: bool = True
    knowledge_enabled: bool = True
    reasoning_enabled: bool = True
    planning_enabled: bool = True
    reflection_enabled: bool = True
    learning_enabled: bool = True
    reasoning_seed: int | None = Field(default=None, ge=0)
    max_reasoning_steps: int = Field(default=100, ge=1)


class StorageConfig(BaseModel):
    """Persistence backend for AURA domain data.

    ``backend`` selects the storage engine:

    - ``memory`` (development default) — no persistence across process restarts
    - ``sqlite`` — local file-backed store with WAL, migrations, transactions
    - ``postgresql`` — reserved; the same :class:`MemoryStore` interface and row
      format apply, but no driver is bundled (PostgreSQL is never a mandatory
      local dependency).

    Production configuration must not silently fall back to in-memory storage:
    :class:`AuraConfig` rejects ``backend=memory`` in the production environment.
    """

    backend: str = Field(default="memory")
    sqlite_path: str = Field(default="data/aura.sqlite3")
    run_migrations: bool = True
    integrity_check_on_open: bool = True

    @field_validator("backend")
    @classmethod
    def _validate_backend(cls, value: str) -> str:
        normalized = value.strip().lower()
        if normalized not in {"memory", "sqlite", "postgresql"}:
            raise ValueError(f"unknown storage backend {value!r}; expected memory|sqlite|postgresql")
        return normalized


class AuraConfig(BaseModel):
    """Root configuration object. Loaded and validated by :class:`ConfigLoader`."""

    schema_version: ConfigSchemaVersion = ConfigSchemaVersion.V1
    environment: Environments = Environments.DEV
    instance_id: str = Field(default="default")
    budgets: BudgetLimits = Field(default_factory=BudgetLimits)
    logging: LoggingConfig = Field(default_factory=LoggingConfig)
    engines: EngineConfig = Field(default_factory=EngineConfig)
    storage: StorageConfig = Field(default_factory=StorageConfig)
    provider_api_key: SecretStr | None = None
    secrets: dict[str, SecretStr] = Field(default_factory=dict)

    @field_validator("instance_id")
    @classmethod
    def _validate_instance(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("instance_id must not be empty")
        return v

    @model_validator(mode="after")
    def _schema_check(self) -> AuraConfig:
        if self.schema_version != ConfigSchemaVersion.V1:
            raise ValueError(f"unsupported config schema version: {self.schema_version}")
        if self.environment is Environments.PRODUCTION and self.storage.backend == "memory":
            raise ValueError(
                "production environment requires a persistent storage backend "
                "(storage.backend = 'sqlite' or 'postgresql'); refusing unsafe in-memory fallback"
            )
        return self

    def model_dump_safe(self) -> dict[str, object]:
        """Dump config with all secret values redacted. Never log raw secrets."""
        dumped = self.model_dump(mode="json")
        dumped["provider_api_key"] = "***REDACTED***" if self.provider_api_key is not None else None
        dumped["secrets"] = {k: "***REDACTED***" for k in self.secrets}
        return dumped


__all__ = [
    "AuraConfig",
    "BudgetLimits",
    "ConfigSchemaVersion",
    "EngineConfig",
    "Environments",
    "LoggingConfig",
    "StorageConfig",
]