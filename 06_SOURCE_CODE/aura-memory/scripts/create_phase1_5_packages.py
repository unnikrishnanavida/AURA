from __future__ import annotations

import textwrap
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]

phase1 = [
    "protocols",
    "decorators",
    "filesystem",
    "networking",
    "dependency_injection",
]
phase2 = [
    "memory_engine",
    "memory_manager",
    "memory_runtime",
    "memory_pool",
    "memory_registry",
    "memory_repository",
    "memory_allocator",
    "memory_controller",
    "memory_scheduler",
    "memory_services",
    "memory_cache",
    "memory_statistics",
    "memory_metrics",
    "memory_health",
    "memory_monitor",
    "memory_events",
]
phase3 = [
    "context_memory",
    "attention_memory",
    "identity_memory",
    "task_memory",
    "conversation_memory",
    "knowledge_memory",
]
phase4 = ["encoding", "decoding", "matching", "fusion", "deduplication"]

PHASES = {
    "phase1": phase1,
    "phase2": phase2,
    "phase3": phase3,
    "phase4": phase4,
}


def write(path: Path, content: str) -> None:
    if path.exists():
        return
    path.write_text(textwrap.dedent(content).lstrip(), encoding="utf-8")


def ensure_package(package: str) -> Path:
    pkg_dir = BASE / package
    pkg_dir.mkdir(parents=True, exist_ok=True)
    return pkg_dir


def common_init(package: str, cls_name: str, exports: list[str]) -> str:
    exports_list = ",\n    ".join([f'"{item}"' for item in exports])
    return f""""""{package.replace('_', ' ').title()} package initializer.

from __future__ import annotations

from .constants import DEFAULT_NAME
from .exceptions import {cls_name}Error
from .models import {cls_name}Model

__all__ = [
    {exports_list}
]
""""""


def create_phase1() -> None:
    for pkg in phase1:
        pkg_dir = ensure_package(pkg)
        if pkg == "protocols":
            write(pkg_dir / "__init__.py", """"""Protocol helpers for AURA Memory.

from __future__ import annotations

from typing import Protocol

__all__ = ["Protocol", "Serializable", "Loader"]


class Serializable(Protocol):
    def to_dict(self) -> dict[str, object]:
        ...


class Loader(Protocol):
    def load(self, source: str) -> object:
        ...
"""""")
            continue
        if pkg == "decorators":
            write(pkg_dir / "__init__.py", """"""Decorator utilities for AURA Memory.""""
            )
            write(pkg_dir / "logging.py", """"""Logging decorator utilities."""

from __future__ import annotations

import functools
import logging
import time
from typing import Callable, ParamSpec, TypeVar

P = ParamSpec("P")
R = TypeVar("R")
logger = logging.getLogger(__name__)


def timing(name: str) -> Callable[[Callable[P, R]], Callable[P, R]]:
    def decorator(func: Callable[P, R]) -> Callable[P, R]:
        @functools.wraps(func)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            start = time.perf_counter()
            result = func(*args, **kwargs)
            duration = time.perf_counter() - start
            logger.info("%s executed in %.6f seconds", name, duration)
            return result

        return wrapper

    return decorator
"""""")
            continue
        if pkg == "filesystem":
            write(pkg_dir / "__init__.py", """"""Filesystem utilities for AURA Memory.""""
            )
            write(pkg_dir / "storage.py", """"""Simple filesystem-backed storage."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


class FileSystemStorage:
    """Persistent JSON-backed filesystem storage."""

    def __init__(self, base_path: str | Path) -> None:
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)

    def save(self, name: str, payload: dict[str, Any]) -> None:
        path = self.base_path / f"{name}.json"
        path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    def load(self, name: str) -> dict[str, Any] | None:
        path = self.base_path / f"{name}.json"
        if not path.exists():
            return None
        return json.loads(path.read_text(encoding="utf-8"))

    def exists(self, name: str) -> bool:
        return (self.base_path / f"{name}.json").exists()
"""""")
            continue
        if pkg == "networking":
            write(pkg_dir / "__init__.py", """"""Networking helpers for AURA Memory.""""

from __future__ import annotations

from ..network import network_engine, network_manager

__all__ = ["network_engine", "network_manager"]
"""""")
            continue
        if pkg == "dependency_injection":
            write(pkg_dir / "__init__.py", """"""Dependency injection alias for AURA Memory.""""

from __future__ import annotations

from ..di import register, resolve

__all__ = ["register", "resolve"]
"""""")
            continue


def create_phase2() -> None:
    for pkg in phase2:
        pkg_dir = ensure_package(pkg)
        cls_name = pkg.replace("memory_", "").title().replace("_", "")
        write(pkg_dir / "__init__.py", f""""""{pkg.replace('_', ' ').title()} package initializer.""""

from __future__ import annotations

from .constants import DEFAULT_NAME
from .exceptions import {cls_name}Error
from .models import {cls_name}Model
from .engine import Engine

__all__ = ["DEFAULT_NAME", "{cls_name}Error", "{cls_name}Model", "Engine"]
"""""")
        write(pkg_dir / "constants.py", f""""""Constants for aura_memory.{pkg}.""""

DEFAULT_NAME = "{pkg}"
"""""")
        write(pkg_dir / "exceptions.py", f""""""Exceptions for aura_memory.{pkg}.""""

class {cls_name}Error(Exception):
    """Base exception for aura_memory.{pkg}."""
    pass
"""""")
        write(pkg_dir / "models.py", f""""""Data models for aura_memory.{pkg}.""""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class {cls_name}Model:
    """Model for aura_memory.{pkg}."""

    id: str = field(default_factory=lambda: "")
    name: str = field(default="{pkg}")
    metadata: dict[str, Any] = field(default_factory=dict)
"""""")
        write(pkg_dir / "engine.py", f""""""Engine for aura_memory.{pkg}.""""

from __future__ import annotations

from typing import Any


class Engine:
    """Engine for aura_memory.{pkg}."""

    def process(self, payload: dict[str, Any]) -> dict[str, Any]:
        if not isinstance(payload, dict):
            raise TypeError("payload must be a dict")
        return {"status": "processed", "module": "{pkg}", "payload": payload}
"""""")


def create_phase3() -> None:
    for pkg in phase3:
        pkg_dir = ensure_package(pkg)
        cls_name = pkg.title().replace("_", "")
        write(pkg_dir / "__init__.py", f""""""{pkg.replace('_', ' ').title()} package initializer.""""

from __future__ import annotations

from .constants import DEFAULT_NAME
from .exceptions import {cls_name}Error
from .models import {cls_name}Model
from .schemas import {cls_name}Schema
from .engine import Engine
from .manager import Manager
from .service import Service

__all__ = [
    "DEFAULT_NAME",
    "{cls_name}Error",
    "{cls_name}Model",
    "{cls_name}Schema",
    "Engine",
    "Manager",
    "Service",
]
"""""")
        write(pkg_dir / "constants.py", f""""""Constants for aura_memory.{pkg}.""""

DEFAULT_NAME = "{pkg}"
"""""")
        write(pkg_dir / "exceptions.py", f""""""Exceptions for aura_memory.{pkg}.""""

class {cls_name}Error(Exception):
    """Base exception for aura_memory.{pkg}."""
    pass
"""""")
        write(pkg_dir / "models.py", f""""""Model for aura_memory.{pkg}.""""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class {cls_name}Model:
    """Data model for aura_memory.{pkg}."""

    id: str = field(default_factory=lambda: "")
    name: str = field(default="{pkg}")
    metadata: dict[str, Any] = field(default_factory=dict)
"""""")
        write(pkg_dir / "schemas.py", f""""""Schema for aura_memory.{pkg}.""""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class {cls_name}Schema:
    """Schema for aura_memory.{pkg}."""

    name: str = field(default="{pkg}")
    version: str = field(default="1.0")
    metadata: dict[str, Any] = field(default_factory=dict)
"""""")
        write(pkg_dir / "engine.py", f""""""Engine for aura_memory.{pkg}.""""

from __future__ import annotations

from typing import Any


class Engine:
    """Engine for aura_memory.{pkg}."""

    def process(self, payload: dict[str, Any]) -> dict[str, Any]:
        if not isinstance(payload, dict):
            raise TypeError("payload must be a dict")
        return {"status": "processed", "module": "{pkg}", "payload": payload}
"""""")
        write(pkg_dir / "manager.py", f""""""Manager for aura_memory.{pkg}.""""

from __future__ import annotations

from typing import Any


class Manager:
    """Manager for aura_memory.{pkg}."""

    def register(self, key: str, item: Any) -> None:
        if not key:
            raise ValueError("key must be non-empty")

    def get(self, key: str) -> Any:
        return None
"""""")
        write(pkg_dir / "service.py", f""""""Service for aura_memory.{pkg}.""""

from __future__ import annotations

from typing import Any


class Service:
    """Service for aura_memory.{pkg}."""

    def execute(self, payload: dict[str, Any]) -> dict[str, Any]:
        if not isinstance(payload, dict):
            raise TypeError("payload must be a dict")
        return {"status": "ok", "module": "{pkg}", "payload": payload}
"""""")


def create_phase4() -> None:
    for pkg in phase4:
        pkg_dir = ensure_package(pkg)
        cls_name = pkg.title().replace("_", "")
        write(pkg_dir / "__init__.py", f""""""{pkg.replace('_', ' ').title()} package initializer.""""

from __future__ import annotations

from .constants import DEFAULT_NAME
from .exceptions import {cls_name}Error
from .algorithm import Algorithm

__all__ = ["DEFAULT_NAME", "{cls_name}Error", "Algorithm"]
"""""")
        write(pkg_dir / "constants.py", f""""""Constants for aura_memory.{pkg}.""""

DEFAULT_NAME = "{pkg}"
"""""")
        write(pkg_dir / "exceptions.py", f""""""Exceptions for aura_memory.{pkg}.""""

class {cls_name}Error(Exception):
    """Base exception for aura_memory.{pkg}."""
    pass
"""""")
        write(pkg_dir / "algorithm.py", f""""""Algorithm implementation for aura_memory.{pkg}.""""

from __future__ import annotations

from typing import Any


class Algorithm:
    """Algorithm for aura_memory.{pkg}."""

    def execute(self, payload: dict[str, Any]) -> dict[str, Any]:
        if not isinstance(payload, dict):
            raise TypeError("payload must be a dict")
        return {"status": "executed", "module": "{pkg}", "payload": payload}
"""""")


if __name__ == "__main__":
    create_phase1()
    create_phase2()
    create_phase3()
    create_phase4()
    print("Created missing phase 1-4 packages")
