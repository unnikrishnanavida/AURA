from __future__ import annotations

import json
import logging
import re
import textwrap
import threading
import time
import uuid
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

ROOT = Path(__file__).resolve().parent.parent
LOG = logging.getLogger('aura_memory.fill_empty_modules')

CATEGORY_PATTERNS: Dict[str, List[str]] = {
    'validator': ['validator'],
    'exceptions': ['exceptions', 'exception'],
    'constants': ['constants', 'const'],
    'models': ['models', 'schemas', 'types'],
    'repository': ['repository', 'registry', 'storage', 'persistence', 'cache'],
    'service': ['engine', 'manager', 'controller', 'service', 'adapter', 'builder', 'orchestrator', 'executor', 'scheduler', 'processor', 'coordinator', 'monitor', 'optimizer', 'analyzer', 'dispatcher', 'router'],
    'api': ['api', 'routes', 'router', 'request', 'response', 'middleware', 'openapi', 'authentication', 'authorization'],
    'utilities': ['utilities', 'helpers', 'logging', 'diagnostics', 'metrics', 'analytics', 'monitoring', 'validation'],
}


def make_class_name(name: str) -> str:
    parts = re.split(r'[_\-.]+', name)
    return ''.join(part.title() for part in parts if part)


def make_constant_name(name: str) -> str:
    return re.sub(r'[^0-9a-zA-Z]+', '_', name).upper()


def is_empty_file(path: Path) -> bool:
    text = path.read_text(encoding='utf-8', errors='ignore')
    lines = [line for line in text.splitlines() if line.strip() and not line.strip().startswith('#')]
    return not lines


def classify_module(module_name: str) -> str:
    lower_name = module_name.lower()
    for category, patterns in CATEGORY_PATTERNS.items():
        if any(pattern == lower_name or pattern in lower_name for pattern in patterns):
            return category
    return 'generic'


def template_init(package_name: str) -> str:
    return textwrap.dedent(
        """AURA Memory {package_name} package initializer.

__all__: List[str] = []
"""
    ).format(package_name=package_name)


def template_constants(package_name: str, safe_name: str) -> str:
    return textwrap.dedent(
        """AURA Memory {package_name} constants.

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
        """AURA Memory {package_name} exceptions.

from __future__ import annotations
from typing import Any, Dict, Optional


class {class_name}Error(Exception):
    '''Base exception for {package_name}.{class_name}.'''

    def __init__(self, message: str, context: Optional[Dict[str, Any]] = None) -> None:
        super().__init__(message)
        self.context = context or {{}}

    def to_dict(self) -> Dict[str, Any]:
        return {{'message': str(self), 'context': self.context}}


__all__ = ["{class_name}Error"]
"""
    ).format(package_name=package_name, class_name=class_name)


def template_validator(package_name: str, module_name: str, class_name: str) -> str:
    return textwrap.dedent(
        """AURA Memory {package_name} validator for {module_name}.

from __future__ import annotations
import logging
from typing import Any

logger = logging.getLogger(__name__)


class {class_name}Validator:
    '''Validator for {package_name}.{module_name}.'''

    def __init__(self, strict: bool = True) -> None:
        self.strict = strict

    def validate(self, data: Any) -> bool:
        '''Validate a payload for {package_name}.{module_name}.'''
        if data is None:
            logger.error("Validation failed because data is None")
            raise ValueError("data cannot be None")
        if self.strict and isinstance(data, str) and not data.strip():
            logger.error("Validation failed because string payload is empty")
            raise ValueError("data may not be empty")
        if self.strict and isinstance(data, dict) and not data:
            logger.warning("Validation received empty dict payload")
        return True

    async def validate_async(self, data: Any) -> bool:
        '''Async validation wrapper.'''
        return self.validate(data)


__all__ = ["{class_name}Validator"]
"""
    ).format(package_name=package_name, module_name=module_name, class_name=class_name)


def template_model(package_name: str, module_name: str, class_name: str) -> str:
    return textwrap.dedent(
        """AURA Memory {package_name} data model for {module_name}.

from __future__ import annotations
import dataclasses
import time
import uuid
from dataclasses import dataclass, field
from typing import Any, Dict

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class {class_name}Model:
    '''Schema model for {package_name}.{module_name}.'''

    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = field(default='unnamed')
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: float = field(default_factory=time.time)

    def to_dict(self) -> Dict[str, Any]:
        return dataclasses.asdict(self)

    @classmethod
    def from_dict(cls, payload: Dict[str, Any]) -> "{class_name}Model":
        return cls(
            id=str(payload.get('id', uuid.uuid4())),
            name=str(payload.get('name', 'unnamed')),
            metadata=dict(payload.get('metadata', {{}})),
            created_at=float(payload.get('created_at', time.time())),
        )


__all__ = ["{class_name}Model"]
"""
    ).format(package_name=package_name, module_name=module_name, class_name=class_name)


def template_repository(package_name: str, module_name: str, class_name: str) -> str:
    return textwrap.dedent(
        """AURA Memory {package_name} repository for {module_name}.

from __future__ import annotations
import logging
import threading
import time
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class {class_name}Repository:
    '''Repository for {package_name}.{module_name}.'''

    def __init__(self, ttl_seconds: int = 3600) -> None:
        self._lock = threading.RLock()
        self._store: Dict[str, Dict[str, Any]] = {{}}
        self._ttl = ttl_seconds
        self._last_updated: Dict[str, float] = {{}}

    def save(self, key: str, item: Dict[str, Any]) -> None:
        '''Save item to the repository with metadata.'''
        if not key:
            raise ValueError("key must be non-empty")
        with self._lock:
            self._store[key] = {{**item, "saved_at": time.time()}}
            self._last_updated[key] = time.time()
            logger.debug("Saved item %s", key)

    def load(self, key: str) -> Optional[Dict[str, Any]]:
        '''Load item by key if it is still valid.'''
        with self._lock:
            item = self._store.get(key)
            if item is None:
                return None
            if time.time() - self._last_updated.get(key, 0.0) > self._ttl:
                self._store.pop(key, None)
                self._last_updated.pop(key, None)
                logger.debug("Expired item %s", key)
                return None
            return item.copy()

    def delete(self, key: str) -> bool:
        '''Delete item by key.'''
        with self._lock:
            self._last_updated.pop(key, None)
            return self._store.pop(key, None) is not None

    def list_keys(self) -> List[str]:
        '''List all valid keys.'''
        with self._lock:
            return list(self._store.keys())

    async def save_async(self, key: str, item: Dict[str, Any]) -> None:
        '''Async save wrapper.'''
        return self.save(key, item)


__all__ = ["{class_name}Repository"]
"""
    ).format(package_name=package_name, module_name=module_name, class_name=class_name)


def template_api(package_name: str, module_name: str, class_name: str) -> str:
    return textwrap.dedent(
        """AURA Memory {package_name} API adapter for {module_name}.

from __future__ import annotations
import logging
from typing import Any, Callable, Dict

logger = logging.getLogger(__name__)


class {class_name}API:
    '''API adapter for {package_name}.{module_name}.'''

    def __init__(self) -> None:
        self._routes: Dict[str, Callable[[Dict[str, Any]], Dict[str, Any]]] = {{}}

    def register_route(self, path: str, handler: Callable[[Dict[str, Any]], Dict[str, Any]]) -> None:
        '''Register an API route.'''
        if not path.startswith('/'):
            raise ValueError("path must start with '/'")
        self._routes[path] = handler
        logger.debug("Registered route %s", path)

    def dispatch(self, path: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        '''Dispatch a request to the registered handler.'''
        handler = self._routes.get(path)
        if handler is None:
            raise ValueError(f"Route not found: {{path}}")
        return handler(payload)

    async def dispatch_async(self, path: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        '''Async dispatch wrapper.'''
        return self.dispatch(path, payload)


__all__ = ["{class_name}API"]
"""
    ).format(package_name=package_name, module_name=module_name, class_name=class_name)


def template_utilities(package_name: str, module_name: str, safe_name: str) -> str:
    return textwrap.dedent(
        """AURA Memory {package_name} utilities for {module_name}.

from __future__ import annotations
import json
import logging
import time
import uuid
from typing import Any, Dict

logger = logging.getLogger(__name__)


def serialize_{safe_name}(payload: Dict[str, Any]) -> str:
    '''Serialize payload to a compact JSON string.'''
    return json.dumps(payload, sort_keys=True, separators=(",", ":"))


def deserialize_{safe_name}(payload: str) -> Dict[str, Any]:
    '''Deserialize payload from JSON.'''
    return json.loads(payload)


def create_default_{safe_name}() -> Dict[str, Any]:
    '''Create a default payload object.'''
    return {{"id": str(uuid.uuid4()), "name": "default-{safe_name}", "created_at": time.time()}}


def normalize_{safe_name}(payload: Dict[str, Any]) -> Dict[str, Any]:
    '''Normalize a payload into a consistent shape.'''
    payload = payload.copy()
    payload.setdefault("id", str(uuid.uuid4()))
    payload.setdefault("name", "default-{safe_name}")
    payload.setdefault("created_at", time.time())
    return payload


__all__ = [
    "serialize_{safe_name}",
    "deserialize_{safe_name}",
    "create_default_{safe_name}",
    "normalize_{safe_name}",
]
"""
    ).format(package_name=package_name, module_name=module_name, safe_name=safe_name)


def template_service(package_name: str, module_name: str, class_name: str) -> str:
    module_lower = module_name.lower()
    if any(token in module_lower for token in ("engine", "optimizer", "simulator", "processor", "controller", "scheduler", "orchestrator", "executor")):
        service_name = class_name if class_name.endswith("Engine") else f"{class_name}Engine"
        return textwrap.dedent(
            """AURA Memory {package_name} engine for {module_name}.

from __future__ import annotations
import logging
import threading
import time
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


class {service_name}:
    '''Engine for {package_name}.{module_name}.'''

    def __init__(self, config: Optional[Dict[str, Any]] = None) -> None:
        self.config = config or {{}}
        self._active = False
        self._lock = threading.RLock()
        self._started_at: Optional[float] = None

    def start(self) -> None:
        '''Start the engine.'''
        with self._lock:
            if self._active:
                return
            self._active = True
            self._started_at = time.time()
            logger.info("Started %s", self.__class__.__name__)

    def shutdown(self) -> None:
        '''Stop the engine.'''
        with self._lock:
            if not self._active:
                return
            self._active = False
            logger.info("Stopped %s", self.__class__.__name__)

    def process(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        '''Process a payload and return a result.'''
        if not isinstance(payload, dict):
            raise TypeError("payload must be a dict")
        return {{"status": "processed", "module": self.__class__.__name__, "payload": payload}}

    def health(self) -> Dict[str, Any]:
        '''Return engine health and status.'''
        return {{"active": self._active, "started_at": self._started_at}}

    async def process_async(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        '''Async process wrapper.'''
        return self.process(payload)


__all__ = ["{service_name}"]
"""
        ).format(package_name=package_name, module_name=module_name, service_name=service_name)

    if any(token in module_lower for token in ("manager", "registry", "coordinator", "allocator")):
        manager_name = class_name if class_name.endswith("Manager") else f"{class_name}Manager"
        return textwrap.dedent(
            """AURA Memory {package_name} manager for {module_name}.

from __future__ import annotations
import logging
import threading
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class {manager_name}:
    '''Manager for {package_name}.{module_name}.'''

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._items: Dict[str, Any] = {{}}

    def register(self, key: str, item: Any) -> None:
        '''Register an item.'''
        if not key:
            raise ValueError("key must be non-empty")
        with self._lock:
            self._items[key] = item
            logger.debug("Registered %s", key)

    def get(self, key: str) -> Optional[Any]:
        '''Get an item by key.'''
        with self._lock:
            return self._items.get(key)

    def list_keys(self) -> List[str]:
        '''List all registered keys.'''
        with self._lock:
            return list(self._items.keys())

    def remove(self, key: str) -> bool:
        '''Remove an item.'''
        with self._lock:
            return self._items.pop(key, None) is not None


__all__ = ["{manager_name}"]
"""
        ).format(package_name=package_name, module_name=module_name, manager_name=manager_name)

    return textwrap.dedent(
        """AURA Memory {package_name} service for {module_name}.

from __future__ import annotations
import logging
import threading
import time
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


class {class_name}:
    '''Service component for {package_name}.{module_name}.'''

    def __init__(self, config: Optional[Dict[str, Any]] = None) -> None:
        self.config = config or {{}}
        self._active = False
        self._lock = threading.RLock()
        self._started_at: Optional[float] = None

    def start(self) -> None:
        '''Start the service.'''
        with self._lock:
            if self._active:
                return
            self._active = True
            self._started_at = time.time()
            logger.info("Started %s", self.__class__.__name__)

    def stop(self) -> None:
        '''Stop the service.'''
        with self._lock:
            if not self._active:
                return
            self._active = False
            logger.info("Stopped %s", self.__class__.__name__)

    def execute(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        '''Execute processing logic.'''
        if not isinstance(payload, dict):
            raise TypeError("payload must be a dict")
        return {{"status": "ok", "module": self.__class__.__name__, "payload": payload}}

    async def execute_async(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        '''Async execution wrapper.'''
        return self.execute(payload)


__all__ = ["{class_name}"]
"""
    ).format(package_name=package_name, module_name=module_name, class_name=class_name)


def template_generic(package_name: str, module_name: str, class_name: str, safe_name: str) -> str:
    module_lower = module_name.lower()
    if any(token in module_lower for token in ("storage", "cache", "database", "registry", "store")):
        return template_repository(package_name, module_name, f"{class_name}Storage")
    if any(token in module_lower for token in ("model", "schema", "record", "entity")):
        return template_model(package_name, module_name, class_name)
    if any(token in module_lower for token in ("api", "router", "endpoint", "service")):
        return template_api(package_name, module_name, class_name)
    if any(token in module_lower for token in ("util", "helper", "serializer", "converter")):
        return template_utilities(package_name, module_name, safe_name)
    return textwrap.dedent(
        """AURA Memory {package_name} generic module for {module_name}.

from __future__ import annotations
import logging
import time
from typing import Any, Dict

logger = logging.getLogger(__name__)


class {class_name}:
    '''Generic module for {package_name}.{module_name}.'''

    def health_check(self) -> bool:
        '''Return whether the module is healthy.'''
        return True

    def info(self) -> Dict[str, Any]:
        '''Return runtime module metadata.'''
        return {{"module": __name__, "class": self.__class__.__name__, "timestamp": time.time()}}

    def describe(self) -> Dict[str, str]:
        '''Return a descriptive summary of this module.'''
        return {{"package": "{package_name}", "module": "{module_name}"}}


__all__ = ["{class_name}"]
"""
    ).format(package_name=package_name, module_name=module_name, class_name=class_name)


def write_module(path: Path) -> None:
    module_name = path.stem
    package_name = path.parent.name or 'aura_memory'
    class_name = make_class_name(module_name) or 'AuraMemory'
    constant_name = make_constant_name(module_name or 'module')
    category = classify_module(module_name)

    if module_name == '__init__':
        content = template_init(package_name)
    elif category == 'constants':
        content = template_constants(package_name, constant_name)
    elif category == 'exceptions':
        content = template_exceptions(package_name, class_name)
    elif category == 'validator':
        content = template_validator(package_name, module_name, class_name)
    elif category == 'models':
        content = template_model(package_name, module_name, class_name)
    elif category == 'repository':
        content = template_repository(package_name, module_name, class_name)
    elif category == 'service':
        content = template_service(package_name, module_name, class_name)
    elif category == 'api':
        content = template_api(package_name, module_name, class_name)
    elif category == 'utilities':
        content = template_utilities(package_name, module_name, constant_name)
    else:
        content = template_generic(package_name, module_name, class_name, constant_name)

    path.write_text(content, encoding='utf-8')


def main() -> None:
    filled = 0
    for path in sorted(ROOT.rglob('*.py')):
        if path.name in {'fill_empty_modules.py', 'audit_aura_memory.py'}:
            continue
        if is_empty_file(path):
            write_module(path)
            filled += 1
            LOG.info('Populated %s', path.relative_to(ROOT))
    LOG.info('Filled %d empty modules', filled)


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO, format='%(levelname)s:%(name)s:%(message)s')
    main()
