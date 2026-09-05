"""Memory factory + policy-in-persistence tests: backend selection and Policy-gated operations on SQLite."""

from __future__ import annotations

import pytest

from aura.config.settings import AuraConfig, Environments, StorageConfig
from aura.foundation.errors import ConfigurationError
from aura.memory.factory import create_memory_store
from aura.memory.models import (
    MemoryType,
    Sensitivity,
)
from aura.memory.policy import MemoryLifecycle
from aura.memory.sqlite_store import SQLiteMemoryStore
from aura.memory.store import InMemoryMemoryStore


def test_factory_defaults_to_memory() -> None:
    store = create_memory_store()
    assert isinstance(store, InMemoryMemoryStore)


def test_factory_selects_sqlite(tmp_path: object) -> None:
    from pathlib import Path

    path = Path(tmp_path) / "f.sqlite3"  # type: ignore[arg-type]
    store = create_memory_store(
        StorageConfig(backend="sqlite", sqlite_path=str(path)),
    )
    assert isinstance(store, SQLiteMemoryStore)
    store.close()  # type: ignore[attr-defined]


def test_factory_rejects_postgresql_interface_only() -> None:
    with pytest.raises(ConfigurationError, match="interface-only"):
        create_memory_store(StorageConfig(backend="postgresql"))


def test_production_config_rejects_memory_backend() -> None:
    with pytest.raises(ValueError):
        AuraConfig(environment=Environments.PRODUCTION)


def test_policy_applies_to_sqlite_store(tmp_path: object) -> None:
    from pathlib import Path

    path = Path(tmp_path) / "policy.sqlite3"  # type: ignore[arg-type]
    store = create_memory_store(
        StorageConfig(backend="sqlite", sqlite_path=str(path)),
    )
    from aura.memory.engine import MemoryEngine

    engine = MemoryEngine(store=store)  # type: ignore[arg-type]
    engine.remember(
        key="public-note", kind=MemoryType.SEMANTIC, content={"text": "hello"},
        sensitivity=Sensitivity.PUBLIC,
    )
    engine.remember(
        key="restricted", kind=MemoryType.SEMANTIC, content={"secret": True},
        sensitivity=Sensitivity.RESTRICTED,
    )
    lifecycle = MemoryLifecycle(engine=engine)
    exported = lifecycle.export(clearance=0)
    assert any(r["key"] == "public-note" for r in exported)
    assert all(r["key"] != "restricted" for r in exported)
    store.close()  # type: ignore[attr-defined]