from __future__ import annotations

import logging
import re
import textwrap
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

ROOT = Path(__file__).resolve().parent.parent
LOG = logging.getLogger("aura_memory.populate_empty_modules_fixed")

COMMON_IMPORTS = textwrap.dedent(
    """\
from __future__ import annotations
import json
import logging
import threading
import time
import uuid
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)
"""
)


def make_class_name(name: str) -> str:
    parts = re.split(r"[_\-\.]+", name)
    return "".join(part.title() for part in parts if part)


def make_safe_name(name: str) -> str:
    return re.sub(r"[^0-9a-zA-Z_]+", "_", name.lower())


def template_init(package_name: str) -> str:
    return textwrap.dedent(
        """\
"""AURA Memory package initializer for {package_name}."""

from __future__ import annotations

__all__: List[str] = []
"""
    ).format(package_name=package_name)


def template_constants(package_name: str, safe_name: str) -> str:
    return textwrap.dedent(
        """\
"""AURA Memory {package_name} constants."""

from __future__ import annotations

DEFAULT_{safe_name}_ENABLED = True
DEFAULT_{safe_name}_INTERVAL_SECONDS = 30
MAX_{safe_name}_ITEMS = 1024

__all__ = [
    "DEFAULT_{safe_name}_ENABLED",
    "DEFAULT_{safe_name}_INTERVAL_SECONDS",
    "MAX_{safe_name}_ITEMS",
]
"""
    ).format(package_name=package_name, safe_name=safe_name)


def template_exceptions(package_name: str, class_name: str) -> str:
    return textwrap.dedent(
        """\
"""AURA Memory {package_name} exceptions."""

from __future__ import annotations
from typing import Any, Dict, Optional


class {class_name}Error(Exception):
    """Base exception for {package_name} exceptions."""

    def __init__(self, message: str, context: Optional[Dict[str, Any]] = None) -> None:
        super().__init__(message)
        self.context = context or {}

    def to_dict(self) -> Dict[str, Any]:
        return {{"message": str(self), "context": self.context}}


__all__ = ["{class_name}Error"]
"""
    ).format(package_name=package_name, class_name=class_name)


def template_validator(package_name: str, module_name: str, class_name: str) -> str:
    return textwrap.dedent(
        """\
"""AURA Memory {package_name} validator."""

{common_imports}


class {class_name}Validator:
    """Validator for {package_name}.{module_name}."""

    def __init__(self, strict: bool = True) -> None:
        self.strict = strict

    def validate(self, data: Any) -> bool:
        """Validate a payload for {package_name}.{module_name}."""
        if data is None:
            logger.error("Validation failed because data is None")
            raise ValueError("data cannot be None")
        if self.strict and isinstance(data, str) and not data.strip():
            logger.error("Validation failed because string payload is empty")
            raise ValueError("data may not be empty")
        return True

    async def validate_async(self, data: Any) -> bool:
        """Async wrapper for validate."""
        return self.validate(data)


__all__ = ["{class_name}Validator"]
"""
    ).format(
        package_name=package_name,
        module_name=module_name,
        class_name=class_name,
        common_imports=COMMON_IMPORTS.strip(),
    )


def template_model(package_name: str, module_name: str, class_name: str) -> str:
    return textwrap.dedent(
        """\
"""AURA Memory {package_name} data model."""

{common_imports}


@dataclass(frozen=True)
class {class_name}Model:
    """Schema model for {package_name}.{module_name}."""

    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = field(default="unnamed")
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: float = field(default_factory=time.time)

    def to_dict(self) -> Dict[str, Any]:
        return {{"id": self.id, "name": self.name, "metadata": self.metadata, "created_at": self.created_at}}

    @classmethod
    def from_dict(cls, payload: Dict[str, Any]) -> "{class_name}Model":
        return cls(
            id=str(payload.get("id", uuid.uuid4())),
            name=str(payload.get("name", "unnamed")),
            metadata=dict(payload.get("metadata", {})),
            created_at=float(payload.get("created_at", time.time())),
        )


__all__ = ["{class_name}Model"]
"""
    ).format(package_name=package_name, module_name=module_name, class_name=class_name, common_imports=COMMON_IMPORTS.strip())


def template_utilities(package_name: str, module_name: str, safe_name: str) -> str:
    return textwrap.dedent(
        """\
"""AURA Memory {package_name} utilities."""

{common_imports}


def serialize_{safe_name}(payload: Dict[str, Any]) -> str:
    """Serialize payload to compact JSON."""
    return json.dumps(payload, sort_keys=True, separators=(",", ":"))


def deserialize_{safe_name}(payload: str) -> Dict[str, Any]:
    """Deserialize JSON payload into a dictionary."""
    return json.loads(payload)


def create_default_{safe_name}() -> Dict[str, Any]:
    """Create a default payload for {package_name}.{module_name}."""
    return {{"id": str(uuid.uuid4()), "name": f"default-{safe_name}", "created_at": time.time()}}


__all__ = [
    "serialize_{safe_name}",
    "deserialize_{safe_name}",
    "create_default_{safe_name}",
]
"""
    ).format(package_name=package_name, module_name=module_name, safe_name=safe_name, common_imports=COMMON_IMPORTS.strip())


def template_repository(package_name: str, module_name: str, class_name: str) -> str:
    return textwrap.dedent(
        """\
"""AURA Memory {package_name} repository."""

{common_imports}


class {class_name}Repository:
    """Repository for {package_name}.{module_name}."""

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._storage: Dict[str, Dict[str, Any]] = {}

    def save(self, key: str, item: Dict[str, Any]) -> None:
        """Save item to repository."""
        if not key:
            raise ValueError("key must be non-empty")
        with self._lock:
            self._storage[key] = item.copy()
            logger.debug("Saved item %s", key)

    def load(self, key: str) -> Optional[Dict[str, Any]]:
        """Load item by key."""
        with self._lock:
            return self._storage.get(key)

    def delete(self, key: str) -> bool:
        """Delete item by key."""
        with self._lock:
            return self._storage.pop(key, None) is not None

    def list_keys(self) -> List[str]:
        """List stored keys."""
        with self._lock:
            return list(self._storage.keys())

    async def save_async(self, key: str, item: Dict[str, Any]) -> None:
        """Async save wrapper."""
        return self.save(key, item)


__all__ = ["{class_name}Repository"]
"""
    ).format(package_name=package_name, module_name=module_name, class_name=class_name, common_imports=COMMON_IMPORTS.strip())


def template_default(package_name: str, module_name: str, class_name: str) -> str:
    return textwrap.dedent(
        """\
"""AURA Memory {package_name} generic module."""

{common_imports}


class {class_name}:
    """Operational shell for {package_name}.{module_name}."""

    def __init__(self) -> None:
        self.instrumentation: Dict[str, Any] = {}

    def ping(self) -> bool:
        """Return health state."""
        return True

    def info(self) -> Dict[str, Any]:
        """Return module metadata."""
        return {{"module": __name__, "class": self.__class__.__name__, "timestamp": time.time()}}


__all__ = ["{class_name}"]
"""
    ).format(package_name=package_name, module_name=module_name, class_name=class_name, common_imports=COMMON_IMPORTS.strip())


def is_empty_file(path: Path) -> bool:
    text = path.read_text(encoding="utf-8", errors="ignore")
    lines = [line for line in text.splitlines() if line.strip() and not line.strip().startswith("#")]
    return len(lines) == 0


def build_module_content(path: Path) -> str:
    module_name = path.stem
    package_name = path.parent.name or "aura_memory"
    class_name = make_class_name(module_name)
    safe_name = make_safe_name(module_name)
    if module_name == "__init__":
        return template_init(package_name)
    if module_name == "constants":
        return template_constants(package_name, safe_name)
    if module_name == "exceptions":
        return template_exceptions(package_name, class_name)
    if module_name == "validator":
        return template_validator(package_name, module_name, class_name)
    if module_name in {"schemas", "models", "types"}:
        return template_model(package_name, module_name, class_name)
    if module_name in {"logging", "utilities", "helpers"}:
        return template_utilities(package_name, module_name, safe_name)
    if module_name in {"repository", "storage", "persistence", "cache", "registry"}:
        return template_repository(package_name, module_name, class_name)
    return template_default(package_name, module_name, class_name)


def main() -> None:
    filled = 0
    for path in sorted(ROOT.rglob("*.py")):
        if path.name.endswith("populate_empty_modules_fixed.py"):
            continue
        if is_empty_file(path):
            path.write_text(build_module_content(path), encoding="utf-8")
            filled += 1
            LOG.info("Populated %s", path.relative_to(ROOT))
    LOG.info("Filled %d empty modules", filled)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s:%(name)s:%(message)s")
    main()
