from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

files = {
    'dependency_injection/__init__.py': '''"""Dependency injection foundation package."""

from __future__ import annotations

from .manager import DependencyContainer
from .services import DependencyInjectionService
from .exceptions import DependencyInjectionError
from .types import DependencyFactory, DependencyName
from .interfaces import DependencyContainerInterface, DependencyInjectorInterface
from .protocols import DependencyProviderProtocol, DependencyInjectorProtocol

__all__ = [
    'DependencyContainer',
    'DependencyInjectionService',
    'DependencyInjectionError',
    'DependencyFactory',
    'DependencyName',
    'DependencyContainerInterface',
    'DependencyInjectorInterface',
    'DependencyProviderProtocol',
    'DependencyInjectorProtocol',
]
''',
    'dependency_injection/exceptions.py': '''"""Exceptions for dependency injection."""

from __future__ import annotations

from typing import Optional, Dict, Any


class DependencyInjectionError(Exception):
    """Base exception for dependency injection failures."""

    def __init__(self, message: str, context: Optional[Dict[str, Any]] = None) -> None:
        super().__init__(message)
        self.context = context or {}

    def to_dict(self) -> Dict[str, Any]:
        return {'message': str(self), 'context': self.context}


__all__ = ['DependencyInjectionError']
''',
    'dependency_injection/types.py': '''"""Type aliases for dependency injection."""

from __future__ import annotations

from typing import Any, Callable, Dict, Protocol

DependencyName = str
DependencyFactory = Callable[[], Any]


class DependencyProvider(Protocol):
    def __call__(self) -> Any:
        ...


__all__ = ['DependencyName', 'DependencyFactory', 'DependencyProvider']
''',
    'dependency_injection/models.py': '''"""Data models for dependency injection."""

from __future__ import annotations

import dataclasses
from dataclasses import dataclass, field
from typing import Any, Dict


@dataclass(frozen=True)
class DependencyDescriptor:
    """Descriptor for a registered dependency."""

    name: str
    provider: Any
    singleton: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            'name': self.name,
            'singleton': self.singleton,
            'metadata': dict(self.metadata),
        }


__all__ = ['DependencyDescriptor']
''',
    'dependency_injection/interfaces.py': '''"""Dependency injection interfaces."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class DependencyContainerInterface(ABC):
    """Abstract interface for dependency containers."""

    @abstractmethod
    def register(self, name: str, factory: Any, singleton: bool = False) -> None:
        pass

    @abstractmethod
    def resolve(self, name: str) -> Any:
        pass

    @abstractmethod
    def clear(self) -> None:
        pass


class DependencyInjectorInterface(ABC):
    """Abstract interface for dependency injectors."""

    @abstractmethod
    def inject(self, target: Any) -> Any:
        pass


__all__ = ['DependencyContainerInterface', 'DependencyInjectorInterface']
''',
    'dependency_injection/protocols.py': '''"""Dependency injection protocols."""

from __future__ import annotations

from typing import Protocol, Any


class DependencyProviderProtocol(Protocol):
    """Protocol for dependency provider callables."""

    def __call__(self) -> Any:
        ...


class DependencyInjectorProtocol(Protocol):
    """Protocol for dependency injector implementations."""

    def inject(self, target: Any) -> Any:
        ...


__all__ = ['DependencyProviderProtocol', 'DependencyInjectorProtocol']
''',
    'dependency_injection/manager.py': '''"""Dependency injection container manager."""

from __future__ import annotations

import logging
import threading
from typing import Any, Dict, Optional

from .exceptions import DependencyInjectionError
from .types import DependencyFactory
from .models import DependencyDescriptor
from .interfaces import DependencyContainerInterface

logger = logging.getLogger(__name__)


class DependencyContainer(DependencyContainerInterface):
    """Thread-safe container for dependency registration and resolution."""

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._providers: Dict[str, DependencyDescriptor] = {}
        self._singletons: Dict[str, Any] = {}

    def register(self, name: str, factory: DependencyFactory, singleton: bool = False) -> None:
        if not name:
            raise DependencyInjectionError('Dependency name must be non-empty')
        if not callable(factory):
            raise DependencyInjectionError('Dependency factory must be callable')
        with self._lock:
            self._providers[name] = DependencyDescriptor(name=name, provider=factory, singleton=singleton)
            logger.debug('Registered dependency %s singleton=%s', name, singleton)

    def resolve(self, name: str) -> Any:
        with self._lock:
            descriptor = self._providers.get(name)
            if descriptor is None:
                raise DependencyInjectionError(f"Dependency '{name}' is not registered")
            if descriptor.singleton:
                if name not in self._singletons:
                    self._singletons[name] = descriptor.provider()
                return self._singletons[name]
            return descriptor.provider()

    def clear(self) -> None:
        with self._lock:
            self._providers.clear()
            self._singletons.clear()
            logger.debug('Cleared dependency container')

    def list_dependencies(self) -> Dict[str, Dict[str, Any]]:
        with self._lock:
            return {name: desc.to_dict() for name, desc in self._providers.items()}


__all__ = ['DependencyContainer']
''',
    'dependency_injection/services.py': '''"""Dependency injection lifecycle service."""

from __future__ import annotations

import logging
import threading
import time
from typing import Any, Dict, Optional

from .manager import DependencyContainer
from .exceptions import DependencyInjectionError

logger = logging.getLogger(__name__)


class DependencyInjectionService:
    """Lifecycle service for dependency injection."""

    def __init__(self, container: Optional[DependencyContainer] = None) -> None:
        self.container = container or DependencyContainer()
        self._active = False
        self._lock = threading.RLock()
        self._started_at: Optional[float] = None

    def start(self) -> None:
        with self._lock:
            if self._active:
                return
            self._active = True
            self._started_at = time.time()
            logger.info('DependencyInjectionService started')

    def stop(self) -> None:
        with self._lock:
            if not self._active:
                return
            self._active = False
            logger.info('DependencyInjectionService stopped')

    def register(self, name: str, factory: Any, singleton: bool = False) -> None:
        if not self._active:
            raise DependencyInjectionError('Service is not active')
        self.container.register(name, factory, singleton)

    def resolve(self, name: str) -> Any:
        if not self._active:
            raise DependencyInjectionError('Service is not active')
        return self.container.resolve(name)

    def health(self) -> Dict[str, Any]:
        return {
            'active': self._active,
            'registered': list(self.container.list_dependencies().keys()),
            'started_at': self._started_at,
        }


__all__ = ['DependencyInjectionService']
''',
    'dependency_injection/engine.py': '''"""Simple dependency injection engine."""

from __future__ import annotations

import logging
import threading
import time
from typing import Any, Dict, Optional

from .services import DependencyInjectionService

logger = logging.getLogger(__name__)


class DependencyInjectionEngine:
    """Engine wrapper around the dependency injection service."""

    def __init__(self, service: Optional[DependencyInjectionService] = None) -> None:
        self.service = service or DependencyInjectionService()
        self._active = False
        self._lock = threading.RLock()
        self._started_at: Optional[float] = None

    def start(self) -> None:
        with self._lock:
            if self._active:
                return
            self.service.start()
            self._active = True
            self._started_at = time.time()
            logger.info('DependencyInjectionEngine started')

    def shutdown(self) -> None:
        with self._lock:
            if not self._active:
                return
            self.service.stop()
            self._active = False
            logger.info('DependencyInjectionEngine stopped')

    def resolve(self, name: str) -> Any:
        if not self._active:
            raise RuntimeError('DependencyInjectionEngine is not active')
        return self.service.resolve(name)

    def health(self) -> Dict[str, Any]:
        return {
            'active': self._active,
            'started_at': self._started_at,
            'service': self.service.health(),
        }


__all__ = ['DependencyInjectionEngine']
''',
    'protocols/__init__.py': '''"""Protocols foundation package."""

from __future__ import annotations

from .manager import ProtocolRegistry
from .services import ProtocolService
from .exceptions import ProtocolError
from .types import ProtocolName
from .interfaces import ProtocolRegistryInterface
from .protocols import ProtocolImplementation

__all__ = [
    'ProtocolRegistry',
    'ProtocolService',
    'ProtocolError',
    'ProtocolName',
    'ProtocolRegistryInterface',
    'ProtocolImplementation',
]
''',
    'protocols/exceptions.py': '''"""Exceptions for protocols."""

from __future__ import annotations

from typing import Any, Dict, Optional


class ProtocolError(Exception):
    """Base protocol error."""

    def __init__(self, message: str, context: Optional[Dict[str, Any]] = None) -> None:
        super().__init__(message)
        self.context = context or {}

    def to_dict(self) -> Dict[str, Any]:
        return {'message': str(self), 'context': self.context}


__all__ = ['ProtocolError']
''',
    'protocols/types.py': '''"""Protocol type aliases."""

from __future__ import annotations

from typing import Any, Callable, Dict, Protocol

ProtocolName = str
ProtocolHandler = Callable[[Dict[str, Any]], Any]


class ProtocolImplementation(Protocol):
    """Base protocol implementation contract."""

    def execute(self, payload: Dict[str, Any]) -> Any:
        ...


__all__ = ['ProtocolName', 'ProtocolHandler', 'ProtocolImplementation']
''',
    'protocols/interfaces.py': '''"""Protocol registry interfaces."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict


class ProtocolRegistryInterface(ABC):
    """Abstract interface for protocol registries."""

    @abstractmethod
    def register(self, name: str, implementation: Any) -> None:
        pass

    @abstractmethod
    def resolve(self, name: str) -> Any:
        pass

    @abstractmethod
    def list_protocols(self) -> Dict[str, Any]:
        pass


__all__ = ['ProtocolRegistryInterface']
''',
    'protocols/protocols.py': '''"""Protocol registry implementation."""

from __future__ import annotations

import logging
from typing import Any, Dict

from .exceptions import ProtocolError
from .interfaces import ProtocolRegistryInterface

logger = logging.getLogger(__name__)


class ProtocolImplementation:
    """A lightweight protocol implementation wrapper."""

    def __init__(self, name: str, handler: Any) -> None:
        if not name:
            raise ProtocolError('Protocol name cannot be empty')
        if not callable(getattr(handler, 'execute', None)) and not callable(handler):
            raise ProtocolError('Protocol handler must be callable or expose execute()')
        self.name = name
        self.handler = handler

    def execute(self, payload: Dict[str, Any]) -> Any:
        if callable(self.handler):
            return self.handler(payload)
        return self.handler.execute(payload)


__all__ = ['ProtocolImplementation']
''',
    'protocols/manager.py': '''"""Protocol registry manager."""

from __future__ import annotations

import logging
import threading
from typing import Any, Dict, Optional

from .interfaces import ProtocolRegistryInterface
from .protocols import ProtocolImplementation
from .exceptions import ProtocolError

logger = logging.getLogger(__name__)


class ProtocolRegistry(ProtocolRegistryInterface):
    """Thread-safe registry of named protocols."""

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._protocols: Dict[str, ProtocolImplementation] = {}

    def register(self, name: str, implementation: Any) -> None:
        if not name:
            raise ProtocolError('Protocol name must be non-empty')
        impl = ProtocolImplementation(name, implementation)
        with self._lock:
            self._protocols[name] = impl
            logger.debug('Registered protocol %s', name)

    def resolve(self, name: str) -> Optional[ProtocolImplementation]:
        with self._lock:
            return self._protocols.get(name)

    def list_protocols(self) -> Dict[str, ProtocolImplementation]:
        with self._lock:
            return dict(self._protocols)


__all__ = ['ProtocolRegistry']
''',
    'protocols/services.py': '''"""Protocol service orchestration."""

from __future__ import annotations

import logging
import threading
import time
from typing import Any, Dict, Optional

from .manager import ProtocolRegistry
from .exceptions import ProtocolError

logger = logging.getLogger(__name__)


class ProtocolService:
    """Service wrapper for protocol registry operations."""

    def __init__(self, registry: Optional[ProtocolRegistry] = None) -> None:
        self.registry = registry or ProtocolRegistry()
        self._active = False
        self._lock = threading.RLock()
        self._started_at: Optional[float] = None

    def start(self) -> None:
        with self._lock:
            if self._active:
                return
            self._active = True
            self._started_at = time.time()
            logger.info('ProtocolService started')

    def stop(self) -> None:
        with self._lock:
            if not self._active:
                return
            self._active = False
            logger.info('ProtocolService stopped')

    def register(self, name: str, implementation: Any) -> None:
        if not self._active:
            raise ProtocolError('ProtocolService is not active')
        self.registry.register(name, implementation)

    def execute(self, name: str, payload: Dict[str, Any]) -> Any:
        if not self._active:
            raise ProtocolError('ProtocolService is not active')
        protocol = self.registry.resolve(name)
        if protocol is None:
            raise ProtocolError(f"Protocol '{name}' not found")
        return protocol.execute(payload)

    def health(self) -> Dict[str, Any]:
        return {
            'active': self._active,
            'protocols': list(self.registry.list_protocols().keys()),
            'started_at': self._started_at,
        }


__all__ = ['ProtocolService']
''',
}

for rel_path, content in files.items():
    path = ROOT / rel_path
    path.write_text(content, encoding='utf-8')
    print(f'Wrote {path}')
''