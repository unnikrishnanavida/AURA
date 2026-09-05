"""Memory store factory.

Selects the persistence backend from validated configuration. This is the only
place that maps ``AuraConfig.storage.backend`` to a concrete :class:`MemoryStore`
implementation, keeping engines backend-agnostic.
"""

from __future__ import annotations

from typing import Any

from aura.config.settings import AuraConfig, StorageConfig
from aura.foundation.errors import ConfigurationError
from aura.memory.store import InMemoryMemoryStore, MemoryStore


def create_memory_store(config: AuraConfig | StorageConfig | None = None, **overrides: Any) -> MemoryStore:
    """Build the configured memory store.

    ``overrides`` may supply ``path``/``clock`` for tests (e.g. a temp path).
    """
    settings = config.storage if isinstance(config, AuraConfig) else config
    if settings is None:
        settings = StorageConfig()
    backend = (overrides.pop("backend", None) or settings.backend).lower()

    if backend == "memory":
        return InMemoryMemoryStore()

    if backend == "sqlite":
        from aura.memory.sqlite_store import SQLiteMemoryStore

        path = overrides.pop("path", settings.sqlite_path)
        return SQLiteMemoryStore(
            path=path,
            run_migrations=settings.run_migrations,
            integrity_check=settings.integrity_check_on_open,
            clock=overrides.get("clock"),
        )

    if backend == "postgresql":
        # Interface-only today; never silently fall back to an in-memory store.
        raise ConfigurationError(
            "storage.backend = 'postgresql' is interface-only in this release; "
            "use 'sqlite' for persistent local storage or implement the "
            "PostgreSQLMemoryStore protocol"
        )

    raise ConfigurationError(f"unknown storage backend {backend!r}")


__all__ = ["create_memory_store"]