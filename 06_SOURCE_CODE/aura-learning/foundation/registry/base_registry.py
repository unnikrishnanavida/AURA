"""
AURA Framework
--------------

Module:
    foundation.registry.base_registry

Description
-----------
Enterprise-grade generic registry engine.

The BaseRegistry provides the foundation for every registry inside
the AURA framework.

Responsibilities
----------------
• Thread-safe object registration
• Generic type-safe storage
• Namespace management
• Fast lookup
• Batch operations
• Validation
• Statistics
• Metrics
• Diagnostics
• Health monitoring
• Snapshot support
• Dependency tracking
• Lifecycle hooks
• Extension points

Every specialized registry inherits from this class.

Author
------
AURA Framework

License
-------
MIT
"""

from __future__ import annotations

# ==========================================================
# Standard Library Imports
# ==========================================================

import fnmatch
import time
import uuid

from abc import ABC
from abc import abstractmethod

from collections import defaultdict

from copy import deepcopy

from dataclasses import dataclass
from dataclasses import field

from datetime import datetime
from enum import Enum
from enum import auto

from threading import RLock

from typing import (
    Any,
    Callable,
    ClassVar,
    Dict,
    Generic,
    Iterator,
    Mapping,
    MutableMapping,
    Optional,
    Type,
    TypeVar,
)

# ==========================================================
# Local Imports
# ==========================================================

from .exceptions import (
    DuplicateRegistrationError,
    EntryNotFoundError,
    RegistryValidationError,
)

# ==========================================================
# Generic Types
# ==========================================================

T = TypeVar("T")

K = TypeVar("K", bound=str)

# ==========================================================
# Registry Status
# ==========================================================

class RegistryState(Enum):
    """
    Current runtime state of the registry.
    """

    CREATED = auto()

    INITIALIZING = auto()

    READY = auto()

    LOCKED = auto()

    DEGRADED = auto()

    SHUTDOWN = auto()

# ==========================================================
# Health
# ==========================================================

class HealthStatus(Enum):

    HEALTHY = auto()

    WARNING = auto()

    DEGRADED = auto()

    CRITICAL = auto()

# ==========================================================
# Registry Entry
# ==========================================================

@dataclass(slots=True)
class RegistryEntry(Generic[T]):
    """
    Represents a single registry entry.
    """

    key: str

    value: T

    namespace: str = "default"

    tags: set[str] = field(default_factory=set)

    metadata: dict[str, Any] = field(default_factory=dict)

    created_at: datetime = field(default_factory=datetime.utcnow)

    updated_at: datetime = field(default_factory=datetime.utcnow)

    version: int = 1

    uid: str = field(
        default_factory=lambda: str(uuid.uuid4())
    )

# ==========================================================
# Registry Statistics
# ==========================================================

@dataclass(slots=True)
class RegistryStatistics:

    registrations: int = 0

    removals: int = 0

    updates: int = 0

    lookups: int = 0

    hits: int = 0

    misses: int = 0

    validations: int = 0

    validation_failures: int = 0

    duplicate_registrations: int = 0

    snapshots: int = 0

# ==========================================================
# Registry Metrics
# ==========================================================

@dataclass(slots=True)
class RegistryMetrics:

    started_at: float = field(
        default_factory=time.perf_counter
    )

    last_registration: float = 0.0

    last_lookup: float = 0.0

    total_lookup_time: float = 0.0

    total_registration_time: float = 0.0

# ==========================================================
# Registry Configuration
# ==========================================================

@dataclass(slots=True)
class RegistryConfiguration:

    allow_overwrite: bool = False

    case_sensitive: bool = True

    enable_validation: bool = True

    enable_statistics: bool = True

    enable_metrics: bool = True

    enable_snapshots: bool = True

    default_namespace: str = "default"

# ==========================================================
# Registry Snapshot
# ==========================================================

@dataclass(slots=True)
class RegistrySnapshot(Generic[T]):

    created_at: datetime

    entries: dict[str, RegistryEntry[T]]

    statistics: RegistryStatistics

# ==========================================================
# Base Registry
# ==========================================================

class BaseRegistry(
    Generic[K, T],
    ABC,
):
    """
    Enterprise-grade registry engine.

    Parent class of every registry in AURA.
    """

    VERSION: ClassVar[str] = "1.0.0"

    def __init__(
        self,
        *,
        configuration: RegistryConfiguration | None = None,
    ) -> None:

        self._lock = RLock()

        self._configuration = (
            configuration
            or RegistryConfiguration()
        )

        self._state = RegistryState.CREATED

        #
        # Primary Storage
        #

        self._entries: dict[
            str,
            RegistryEntry[T],
        ] = {}

        #
        # Namespace Index
        #

        self._namespaces: defaultdict[
            str,
            set[str],
        ] = defaultdict(set)

        #
        # Type Index
        #

        self._type_index: defaultdict[
            type,
            set[str],
        ] = defaultdict(set)

        #
        # Dependency Graph
        #

        self._dependencies: defaultdict[
            str,
            set[str],
        ] = defaultdict(set)

        #
        # Reverse Dependency Graph
        #

        self._dependents: defaultdict[
            str,
            set[str],
        ] = defaultdict(set)

        #
        # Snapshots
        #

        self._snapshots: list[
            RegistrySnapshot[T]
        ] = []

        #
        # Runtime
        #

        self._statistics = RegistryStatistics()

        self._metrics = RegistryMetrics()

        self._health = HealthStatus.HEALTHY

        self._initialize()

    # ======================================================
    # Initialization
    # ======================================================

    def _initialize(self) -> None:
        """
        Initialize registry runtime.
        """

        self._state = RegistryState.INITIALIZING

        self.initialize()

        self._state = RegistryState.READY

    # ======================================================
    # Abstract Hooks
    # ======================================================

    @abstractmethod
    def validate(
        self,
        key: str,
        value: T,
    ) -> None:
        """
        Validate a registry entry.

        Must be implemented by subclasses.
        """

        raise NotImplementedError

    def initialize(
        self,
    ) -> None:
        """
        Optional initialization hook.
        """

        return

    # ======================================================
    # Internal Validation
    # ======================================================

    def _validate_key(
        self,
        key: str,
    ) -> str:

        if not isinstance(
            key,
            str,
        ):

            raise RegistryValidationError(
                "Registry key must be a string."
            )

        key = key.strip()

        if not key:

            raise RegistryValidationError(
                "Registry key cannot be empty."
            )

        if (
            not self._configuration.case_sensitive
        ):

            key = key.lower()

        return key

    def _validate_registration(
        self,
        key: str,
        value: T,
    ) -> str:

        key = self._validate_key(
            key,
        )

        self._statistics.validations += 1

        self.validate(
            key,
            value,
        )

        return key
        # ======================================================
    # Registration Engine
    # ======================================================

    def register(
        self,
        key: str,
        value: T,
        *,
        namespace: str | None = None,
        tags: set[str] | None = None,
        metadata: dict[str, Any] | None = None,
        overwrite: bool = False,
    ) -> RegistryEntry[T]:
        """
        Register an object inside the registry.
        """

        with self._lock:

            started = time.perf_counter()

            namespace = (
                namespace
                or self._configuration.default_namespace
            )

            key = self._validate_registration(
                key,
                value,
            )

            if (
                key in self._entries
                and
                not overwrite
                and
                not self._configuration.allow_overwrite
            ):

                self._statistics.duplicate_registrations += 1

                raise DuplicateRegistrationError(
                    f"'{key}' is already registered."
                )

            entry = RegistryEntry(

                key=key,

                value=value,

                namespace=namespace,

                tags=tags or set(),

                metadata=metadata or {},

            )

            self.before_register(entry)

            self._entries[key] = entry

            self._namespaces[
                namespace
            ].add(key)

            self._type_index[
                type(value)
            ].add(key)

            self._statistics.registrations += 1

            self._metrics.last_registration = (
                time.perf_counter()
            )

            self._metrics.total_registration_time += (
                self._metrics.last_registration
                - started
            )

            self.after_register(entry)

            return entry

    # ======================================================
    # Batch Registration
    # ======================================================

    def register_many(
        self,
        entries: Mapping[str, T],
        *,
        namespace: str | None = None,
    ) -> list[RegistryEntry[T]]:
        """
        Register multiple objects.
        """

        results = []

        with self._lock:

            for key, value in entries.items():

                results.append(

                    self.register(

                        key,

                        value,

                        namespace=namespace,

                    )

                )

        return results

    # ======================================================
    # Replace
    # ======================================================

    def replace(
        self,
        key: str,
        value: T,
    ) -> RegistryEntry[T]:
        """
        Replace an existing registry entry.
        """

        return self.register(

            key,

            value,

            overwrite=True,

        )

    # ======================================================
    # Lookup Engine
    # ======================================================

    def get(
        self,
        key: str,
        default: T | None = None,
    ) -> T | None:
        """
        Retrieve a registry value.
        """

        started = time.perf_counter()

        with self._lock:

            key = self._validate_key(
                key,
            )

            self.before_lookup(
                key,
            )

            self._statistics.lookups += 1

            entry = self._entries.get(
                key,
            )

            self._metrics.last_lookup = (
                time.perf_counter()
            )

            self._metrics.total_lookup_time += (
                self._metrics.last_lookup
                - started
            )

            if entry is None:

                self._statistics.misses += 1

                self.after_lookup(
                    key,
                    None,
                )

                return default

            self._statistics.hits += 1

            self.after_lookup(
                key,
                entry,
            )

            return entry.value

    def get_entry(
        self,
        key: str,
    ) -> RegistryEntry[T]:
        """
        Return the RegistryEntry.
        """

        key = self._validate_key(
            key,
        )

        entry = self._entries.get(
            key,
        )

        if entry is None:

            raise EntryNotFoundError(
                f"'{key}' not found."
            )

        return entry

    def require(
        self,
        key: str,
    ) -> T:
        """
        Retrieve a required object.
        """

        value = self.get(
            key,
        )

        if value is None:

            raise EntryNotFoundError(
                f"'{key}' does not exist."
            )

        return value

    # ======================================================
    # Namespace Operations
    # ======================================================

    def namespace(
        self,
        namespace: str,
    ) -> dict[str, T]:
        """
        Return all objects inside a namespace.
        """

        with self._lock:

            result = {}

            for key in self._namespaces.get(
                namespace,
                set(),
            ):

                result[key] = (
                    self._entries[key].value
                )

            return result

    def namespaces(
        self,
    ) -> tuple[str, ...]:
        """
        Return all namespaces.
        """

        return tuple(
            sorted(
                self._namespaces.keys()
            )
        )

    # ======================================================
    # Queries
    # ======================================================

    def contains(
        self,
        key: str,
    ) -> bool:

        return (
            self._validate_key(key)
            in self._entries
        )

    def exists(
        self,
        key: str,
    ) -> bool:

        return self.contains(
            key,
        )

    @property
    def size(
        self,
    ) -> int:

        return len(
            self._entries
        )

    def is_empty(
        self,
    ) -> bool:

        return self.size == 0

    # ======================================================
    # Removal Engine
    # ======================================================

    def remove(
        self,
        key: str,
    ) -> RegistryEntry[T]:
        """
        Remove an object.
        """

        with self._lock:

            entry = self.get_entry(
                key,
            )

            self.before_remove(
                entry,
            )

            del self._entries[
                entry.key
            ]

            self._namespaces[
                entry.namespace
            ].discard(
                entry.key
            )

            self._type_index[
                type(entry.value)
            ].discard(
                entry.key
            )

            self._statistics.removals += 1

            self.after_remove(
                entry,
            )

            return entry

    def clear(
        self,
    ) -> None:
        """
        Remove everything.
        """

        with self._lock:

            self._entries.clear()

            self._namespaces.clear()

            self._type_index.clear()

            self._dependencies.clear()

            self._dependents.clear()

    # ======================================================
    # Iteration
    # ======================================================

    def keys(
        self,
    ) -> tuple[str, ...]:

        return tuple(
            self._entries.keys()
        )

    def values(
        self,
    ) -> tuple[T, ...]:

        return tuple(

            entry.value

            for entry

            in self._entries.values()

        )

    def items(
        self,
    ) -> tuple[tuple[str, T], ...]:

        return tuple(

            (
                key,
                entry.value,
            )

            for key, entry

            in self._entries.items()

        )

    def __contains__(
        self,
        key: object,
    ) -> bool:

        if not isinstance(
            key,
            str,
        ):
            return False

        return self.contains(
            key,
        )

    def __len__(
        self,
    ) -> int:

        return self.size

    def __iter__(
        self,
    ) -> Iterator[str]:

        return iter(
            self._entries
        )
        # ======================================================
    # Dependency Management
    # ======================================================

    def add_dependency(
        self,
        source: str,
        dependency: str,
    ) -> None:
        """
        Register a dependency relationship.

        source -> dependency
        """

        with self._lock:

            source = self._validate_key(source)
            dependency = self._validate_key(dependency)

            if source == dependency:
                raise RegistryValidationError(
                    "A registry entry cannot depend on itself."
                )

            if source not in self._entries:
                raise EntryNotFoundError(
                    f"Source '{source}' does not exist."
                )

            if dependency not in self._entries:
                raise EntryNotFoundError(
                    f"Dependency '{dependency}' does not exist."
                )

            self._dependencies[source].add(dependency)
            self._dependents[dependency].add(source)

            self._detect_circular_dependency(source)


    def remove_dependency(
        self,
        source: str,
        dependency: str,
    ) -> None:
        """
        Remove a dependency relationship.
        """

        with self._lock:

            self._dependencies[source].discard(dependency)
            self._dependents[dependency].discard(source)


    def dependencies(
        self,
        key: str,
    ) -> tuple[str, ...]:
        """
        Return direct dependencies.
        """

        key = self._validate_key(key)

        return tuple(
            sorted(
                self._dependencies.get(
                    key,
                    set(),
                )
            )
        )


    def dependents(
        self,
        key: str,
    ) -> tuple[str, ...]:
        """
        Return direct dependents.
        """

        key = self._validate_key(key)

        return tuple(
            sorted(
                self._dependents.get(
                    key,
                    set(),
                )
            )
        )


    # ======================================================
    # Circular Dependency Detection
    # ======================================================

    def _detect_circular_dependency(
        self,
        start: str,
    ) -> None:
        """
        Detect circular dependencies using DFS.
        """

        visited: set[str] = set()

        stack: set[str] = set()

        def visit(node: str) -> None:

            if node in stack:

                raise RegistryValidationError(
                    f"Circular dependency detected at '{node}'."
                )

            if node in visited:
                return

            visited.add(node)
            stack.add(node)

            for dependency in self._dependencies.get(
                node,
                (),
            ):
                visit(dependency)

            stack.remove(node)

        visit(start)


    # ======================================================
    # Search Engine
    # ======================================================

    def search(
        self,
        pattern: str,
    ) -> dict[str, T]:
        """
        Search registry keys using wildcard patterns.

        Example:

            registry.search("*engine*")
        """

        with self._lock:

            result: dict[str, T] = {}

            for key, entry in self._entries.items():

                if fnmatch.fnmatch(
                    key,
                    pattern,
                ):
                    result[key] = entry.value

            return result


    def search_namespace(
        self,
        namespace: str,
    ) -> dict[str, T]:
        """
        Search by namespace.
        """

        return self.namespace(
            namespace,
        )


    def search_type(
        self,
        object_type: type,
    ) -> dict[str, T]:
        """
        Search by object type.
        """

        with self._lock:

            result = {}

            for key in self._type_index.get(
                object_type,
                set(),
            ):

                result[key] = (
                    self._entries[key].value
                )

            return result


    # ======================================================
    # Filtering
    # ======================================================

    def filter(
        self,
        predicate: Callable[
            [RegistryEntry[T]],
            bool,
        ],
    ) -> dict[str, T]:
        """
        Filter registry entries.
        """

        with self._lock:

            result = {}

            for key, entry in self._entries.items():

                if predicate(entry):

                    result[key] = entry.value

            return result


    def filter_tags(
        self,
        *tags: str,
    ) -> dict[str, T]:
        """
        Return entries matching every tag.
        """

        required = set(tags)

        return self.filter(

            lambda entry:

            required.issubset(
                entry.tags
            )

        )


    def filter_metadata(
        self,
        key: str,
        value: Any,
    ) -> dict[str, T]:
        """
        Filter by metadata.
        """

        return self.filter(

            lambda entry:

            entry.metadata.get(key)
            == value

        )


    # ======================================================
    # Bulk Queries
    # ======================================================

    def entries(
        self,
    ) -> tuple[RegistryEntry[T], ...]:
        """
        Return every registry entry.
        """

        return tuple(
            self._entries.values()
        )


    def first(
        self,
    ) -> RegistryEntry[T] | None:
        """
        Return the first registry entry.
        """

        for entry in self._entries.values():
            return entry

        return None


    def last(
        self,
    ) -> RegistryEntry[T] | None:
        """
        Return the last registry entry.
        """

        if not self._entries:
            return None

        return next(
            reversed(
                self._entries.values()
            )
        )


    # ======================================================
    # Sorting
    # ======================================================

    def sorted_keys(
        self,
    ) -> tuple[str, ...]:
        """
        Return sorted registry keys.
        """

        return tuple(
            sorted(
                self._entries.keys()
            )
        )


    def sorted_entries(
        self,
    ) -> tuple[RegistryEntry[T], ...]:
        """
        Return sorted registry entries.
        """

        return tuple(

            sorted(

                self._entries.values(),

                key=lambda entry: entry.key,

            )

        )
        # ======================================================
    # Snapshot Engine
    # ======================================================

    def create_snapshot(
        self,
    ) -> RegistrySnapshot[T]:
        """
        Create a complete registry snapshot.
        """

        with self._lock:

            snapshot = RegistrySnapshot(

                created_at=datetime.utcnow(),

                entries=deepcopy(
                    self._entries
                ),

                statistics=deepcopy(
                    self._statistics
                ),

            )

            self._snapshots.append(
                snapshot
            )

            self._statistics.snapshots += 1

            return snapshot


    def restore_snapshot(
        self,
        snapshot: RegistrySnapshot[T],
    ) -> None:
        """
        Restore a previously created snapshot.
        """

        with self._lock:

            self.clear()

            self._entries = deepcopy(
                snapshot.entries
            )

            self._statistics = deepcopy(
                snapshot.statistics
            )

            #
            # Rebuild indexes
            #

            for key, entry in self._entries.items():

                self._namespaces[
                    entry.namespace
                ].add(key)

                self._type_index[
                    type(entry.value)
                ].add(key)


    def latest_snapshot(
        self,
    ) -> RegistrySnapshot[T] | None:
        """
        Return the latest snapshot.
        """

        if not self._snapshots:

            return None

        return self._snapshots[-1]


    def clear_snapshots(
        self,
    ) -> None:
        """
        Remove all stored snapshots.
        """

        with self._lock:

            self._snapshots.clear()


    # ======================================================
    # Serialization
    # ======================================================

    def to_dict(
        self,
    ) -> dict[str, Any]:
        """
        Serialize the registry into a dictionary.
        """

        with self._lock:

            return {

                "version": self.VERSION,

                "state": self._state.name,

                "entries": {

                    key: {

                        "namespace": entry.namespace,

                        "tags": list(entry.tags),

                        "metadata": deepcopy(
                            entry.metadata
                        ),

                        "created_at": (
                            entry.created_at.isoformat()
                        ),

                        "updated_at": (
                            entry.updated_at.isoformat()
                        ),

                        "version": entry.version,

                    }

                    for key, entry

                    in self._entries.items()

                },

                "statistics": vars(
                    self._statistics
                ),

            }


    def export(
        self,
    ) -> dict[str, Any]:
        """
        Export registry state.
        """

        return self.to_dict()


    # ======================================================
    # Diagnostics
    # ======================================================

    def diagnostics(
        self,
    ) -> dict[str, Any]:
        """
        Return runtime diagnostics.
        """

        return {

            "registry": (
                self.__class__.__name__
            ),

            "version": (
                self.VERSION
            ),

            "state": (
                self._state.name
            ),

            "health": (
                self._health.name
            ),

            "entries": (
                self.size
            ),

            "namespaces": (
                len(
                    self._namespaces
                )
            ),

            "types": (
                len(
                    self._type_index
                )
            ),

            "snapshots": (
                len(
                    self._snapshots
                )
            ),

        }


    # ======================================================
    # Statistics
    # ======================================================

    def statistics(
        self,
    ) -> RegistryStatistics:
        """
        Return runtime statistics.
        """

        return deepcopy(
            self._statistics
        )


    def metrics(
        self,
    ) -> RegistryMetrics:
        """
        Return runtime metrics.
        """

        return deepcopy(
            self._metrics
        )


    def summary(
        self,
    ) -> dict[str, Any]:
        """
        Return registry summary.
        """

        return {

            "entries": self.size,

            "health": self._health.name,

            "state": self._state.name,

            "registrations": (
                self._statistics.registrations
            ),

            "lookups": (
                self._statistics.lookups
            ),

            "hits": (
                self._statistics.hits
            ),

            "misses": (
                self._statistics.misses
            ),

        }


    # ======================================================
    # Health
    # ======================================================

    def health(
        self,
    ) -> HealthStatus:
        """
        Return registry health.
        """

        return self._health


    def check_health(
        self,
    ) -> HealthStatus:
        """
        Perform a health check.
        """

        with self._lock:

            if self._state is RegistryState.DEGRADED:

                self._health = (
                    HealthStatus.DEGRADED
                )

            elif self.size == 0:

                self._health = (
                    HealthStatus.WARNING
                )

            else:

                self._health = (
                    HealthStatus.HEALTHY
                )

            return self._health


    # ======================================================
    # Maintenance
    # ======================================================

    def reset_statistics(
        self,
    ) -> None:
        """
        Reset runtime statistics.
        """

        with self._lock:

            self._statistics = (
                RegistryStatistics()
            )

            self._metrics = (
                RegistryMetrics()
            )


    def reset(
        self,
    ) -> None:
        """
        Reset the registry.
        """

        with self._lock:

            self.clear()

            self.clear_snapshots()

            self.reset_statistics()

            self._state = (
                RegistryState.READY
            )
                # ======================================================
    # Lifecycle Hooks
    # ======================================================

    def before_register(
        self,
        entry: RegistryEntry[T],
    ) -> None:
        """
        Executed before registration.
        """
        return


    def after_register(
        self,
        entry: RegistryEntry[T],
    ) -> None:
        """
        Executed after registration.
        """
        return


    def before_remove(
        self,
        entry: RegistryEntry[T],
    ) -> None:
        """
        Executed before removal.
        """
        return


    def after_remove(
        self,
        entry: RegistryEntry[T],
    ) -> None:
        """
        Executed after removal.
        """
        return


    def before_lookup(
        self,
        key: str,
    ) -> None:
        """
        Executed before lookup.
        """
        return


    def after_lookup(
        self,
        key: str,
        entry: RegistryEntry[T] | None,
    ) -> None:
        """
        Executed after lookup.
        """
        return


    def on_error(
        self,
        exception: Exception,
    ) -> None:
        """
        Global registry error hook.
        """
        return


    # ======================================================
    # Context Manager
    # ======================================================

    def __enter__(
        self,
    ) -> Self:
        """
        Enter registry context.
        """

        return self


    def __exit__(
        self,
        exc_type,
        exc,
        traceback,
    ) -> None:
        """
        Leave registry context.
        """

        self.shutdown()


    # ======================================================
    # Runtime
    # ======================================================

    @property
    def state(
        self,
    ) -> RegistryState:
        """
        Current registry state.
        """

        return self._state


    @property
    def configuration(
        self,
    ) -> RegistryConfiguration:
        """
        Registry configuration.
        """

        return self._configuration


    def shutdown(
        self,
    ) -> None:
        """
        Shutdown registry.
        """

        with self._lock:

            self._state = (
                RegistryState.SHUTDOWN
            )


    # ======================================================
    # Copy Support
    # ======================================================

    def copy(
        self,
    ) -> Self:
        """
        Deep copy this registry.
        """

        registry = self.__class__(

            configuration=deepcopy(
                self._configuration
            )

        )

        for entry in self._entries.values():

            registry.register(

                key=entry.key,

                value=deepcopy(
                    entry.value
                ),

                namespace=entry.namespace,

                tags=set(
                    entry.tags
                ),

                metadata=deepcopy(
                    entry.metadata
                ),

            )

        return registry


    # ======================================================
    # Equality
    # ======================================================

    def __eq__(
        self,
        other: object,
    ) -> bool:

        if not isinstance(
            other,
            BaseRegistry,
        ):
            return False

        return (

            self._entries
            ==
            other._entries

            and

            self._configuration
            ==
            other._configuration

        )


    def __hash__(
        self,
    ) -> int:

        return hash(

            (

                self.__class__.__name__,

                id(self),

            )

        )


    # ======================================================
    # Representation
    # ======================================================

    def __repr__(
        self,
    ) -> str:

        return (

            f"{self.__class__.__name__}("

            f"entries={self.size}, "

            f"state={self._state.name}, "

            f"health={self._health.name})"

        )


    # ======================================================
    # Utility
    # ======================================================

    def empty(
        self,
    ) -> bool:
        """
        Alias for is_empty().
        """

        return self.is_empty()


    def uptime(
        self,
    ) -> float:
        """
        Registry uptime in seconds.
        """

        return (

            time.perf_counter()

            -

            self._metrics.started_at

        )


    # ======================================================
    # Export Helpers
    # ======================================================

    def export_summary(
        self,
    ) -> dict[str, Any]:
        """
        Lightweight export.
        """

        return {

            "entries": self.size,

            "health": self._health.name,

            "state": self._state.name,

            "uptime": self.uptime(),

        }


    # ======================================================
    # Public API
    # ======================================================

    def __bool__(
        self,
    ) -> bool:

        return not self.empty()


    def __getitem__(
        self,
        key: str,
    ) -> T:

        return self.require(
            key,
        )


    def __setitem__(
        self,
        key: str,
        value: T,
    ) -> None:

        self.register(
            key,
            value,
        )


    def __delitem__(
        self,
        key: str,
    ) -> None:

        self.remove(
            key,
        )


# ==========================================================
# Public Exports
# ==========================================================

__all__ = [

    "RegistryState",

    "HealthStatus",

    "RegistryEntry",

    "RegistryStatistics",

    "RegistryMetrics",

    "RegistrySnapshot",

    "RegistryConfiguration",

    "BaseRegistry",

]