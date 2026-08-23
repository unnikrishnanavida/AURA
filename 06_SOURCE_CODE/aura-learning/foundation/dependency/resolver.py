"""
AURA Framework

Dependency Resolver

Enterprise dependency resolution engine.

Responsibilities
----------------
• Dependency Resolution
• Resolution Planning
• Dependency Graph Traversal
• Circular Dependency Detection
• Resolution Optimization
• Resolution Cache
"""

from __future__ import annotations

import threading
import time

from collections import defaultdict
from collections import deque

from dataclasses import dataclass
from dataclasses import field

from typing import (
    Any,
    TypeVar,
)

from .container import (
    DependencyContainer,
)

from .exceptions import (
    CircularDependencyError,
    ResolutionError,
)

# ==========================================================
# Generic Types
# ==========================================================

T = TypeVar("T")

# ==========================================================
# Statistics
# ==========================================================

@dataclass(slots=True)
class ResolverStatistics:

    resolutions: int = 0

    cache_hits: int = 0

    graph_traversals: int = 0

    cycle_checks: int = 0

    failures: int = 0


# ==========================================================
# Metrics
# ==========================================================

@dataclass(slots=True)
class ResolverMetrics:

    started_at: float = field(
        default_factory=time.perf_counter,
    )

    last_resolution: float = 0.0

    total_resolution_time: float = 0.0


# ==========================================================
# Resolver
# ==========================================================

class DependencyResolver:
    """
    Enterprise Dependency Resolver.
    """

    VERSION = "1.0.0"

    def __init__(
        self,
        container: DependencyContainer,
    ) -> None:

        self._container = container

        self._lock = threading.RLock()

        #
        # Resolution Cache
        #

        self._cache: dict[
            str,
            Any,
        ] = {}

        #
        # Dependency Graph Cache
        #

        self._graph_cache: dict[
            str,
            tuple[str, ...],
        ] = {}

        #
        # Runtime
        #

        self._statistics = (
            ResolverStatistics()
        )

        self._metrics = (
            ResolverMetrics()
        )

    # ======================================================
    # Resolution
    # ======================================================

    def resolve(
        self,
        key: str,
        *,
        cached: bool = True,
    ) -> Any:
        """
        Resolve a dependency.
        """

        with self._lock:

            started = time.perf_counter()

            if (

                cached

                and

                key in self._cache

            ):

                self._statistics.cache_hits += 1

                return self._cache[
                    key
                ]

            try:

                instance = self._container.resolve(
                    key,
                )

                self._statistics.resolutions += 1

                elapsed = (

                    time.perf_counter()

                    -

                    started

                )

                self._metrics.last_resolution = (
                    elapsed
                )

                self._metrics.total_resolution_time += (
                    elapsed
                )

                if cached:

                    self._cache[
                        key
                    ] = instance

                return instance

            except Exception as exc:

                self._statistics.failures += 1

                raise ResolutionError(
                    str(exc),
                ) from exc


    # ======================================================
    # Batch Resolution
    # ======================================================

    def resolve_many(
        self,
        *keys: str,
    ) -> tuple[Any, ...]:
        """
        Resolve multiple dependencies.
        """

        return tuple(

            self.resolve(
                key,
            )

            for key

            in keys

        )


    # ======================================================
    # Graph
    # ======================================================

    def dependency_graph(
        self,
    ) -> dict[str, tuple[str, ...]]:
        """
        Return dependency graph.
        """

        self._statistics.graph_traversals += 1

        graph = self._container.dependency_graph()

        self._graph_cache = graph

        return graph


    # ======================================================
    # Dependency Lookup
    # ======================================================

    def dependencies(
        self,
        key: str,
    ) -> tuple[str, ...]:
        """
        Return dependencies of a service.
        """

        return self._container.dependencies(
            key,
        )


    def dependents(
        self,
        key: str,
    ) -> tuple[str, ...]:
        """
        Return reverse dependencies.
        """

        return self._container.dependents(
            key,
        )
        # ======================================================
    # Circular Dependency Detection
    # ======================================================

    def detect_cycles(
        self,
    ) -> tuple[tuple[str, ...], ...]:
        """
        Detect circular dependencies in the graph.
        """

        self._statistics.cycle_checks += 1

        graph = self.dependency_graph()

        visited: set[str] = set()

        stack: set[str] = set()

        cycles: list[tuple[str, ...]] = []

        path: list[str] = []

        def visit(node: str) -> None:

            if node in stack:

                index = path.index(node)

                cycles.append(

                    tuple(

                        path[index:] + [node]

                    )

                )

                return

            if node in visited:

                return

            visited.add(node)

            stack.add(node)

            path.append(node)

            for dependency in graph.get(
                node,
                (),
            ):

                visit(
                    dependency,
                )

            path.pop()

            stack.remove(node)

        for node in graph:

            visit(node)

        return tuple(cycles)


    def validate_graph(
        self,
    ) -> bool:
        """
        Validate dependency graph.
        """

        cycles = self.detect_cycles()

        if cycles:

            raise CircularDependencyError(

                f"Circular dependency "

                f"detected: {cycles}"

            )

        return True


    # ======================================================
    # Topological Sort
    # ======================================================

    def topological_sort(
        self,
    ) -> tuple[str, ...]:
        """
        Compute dependency resolution order.
        """

        graph = self.dependency_graph()

        indegree: dict[str, int] = {

            node: 0

            for node

            in graph

        }

        for dependencies in graph.values():

            for dependency in dependencies:

                indegree.setdefault(
                    dependency,
                    0,
                )

                indegree[
                    dependency
                ] += 1

        queue = deque(

            node

            for node, degree

            in indegree.items()

            if degree == 0

        )

        order: list[str] = []

        while queue:

            node = queue.popleft()

            order.append(
                node,
            )

            for dependency in graph.get(
                node,
                (),
            ):

                indegree[
                    dependency
                ] -= 1

                if (

                    indegree[
                        dependency
                    ]

                    ==

                    0

                ):

                    queue.append(
                        dependency,
                    )

        if len(order) != len(indegree):

            raise CircularDependencyError(

                "Dependency graph "

                "contains cycles."

            )

        return tuple(order)


    # ======================================================
    # Resolution Planning
    # ======================================================

    def resolution_plan(
        self,
        key: str,
    ) -> tuple[str, ...]:
        """
        Return dependency resolution plan.
        """

        plan: list[str] = []

        visited: set[str] = set()

        def build(
            node: str,
        ) -> None:

            if node in visited:

                return

            visited.add(node)

            for dependency in self.dependencies(
                node,
            ):

                build(
                    dependency,
                )

            plan.append(
                node,
            )

        build(
            key,
        )

        return tuple(plan)


    # ======================================================
    # Graph Traversal
    # ======================================================

    def traverse(
        self,
        root: str,
    ) -> tuple[str, ...]:
        """
        Traverse dependency graph.
        """

        visited: set[str] = set()

        result: list[str] = []

        def dfs(
            node: str,
        ) -> None:

            if node in visited:

                return

            visited.add(node)

            result.append(
                node,
            )

            for dependency in self.dependencies(
                node,
            ):

                dfs(
                    dependency,
                )

        dfs(
            root,
        )

        return tuple(result)


    def breadth_first(
        self,
        root: str,
    ) -> tuple[str, ...]:
        """
        Breadth-first traversal.
        """

        queue = deque(
            [root],
        )

        visited = {root}

        result: list[str] = []

        while queue:

            node = queue.popleft()

            result.append(
                node,
            )

            for dependency in self.dependencies(
                node,
            ):

                if dependency not in visited:

                    visited.add(
                        dependency,
                    )

                    queue.append(
                        dependency,
                    )

        return tuple(result)
        # ======================================================
    # Resolution Profiling
    # ======================================================

    def profile(
        self,
        key: str,
    ) -> dict[str, Any]:
        """
        Profile dependency resolution.
        """

        started = time.perf_counter()

        instance = self.resolve(
            key,
            cached=False,
        )

        elapsed = (

            time.perf_counter()

            -

            started

        )

        return {

            "dependency":

                key,

            "instance":

                type(instance).__name__,

            "resolution_time":

                elapsed,

            "cached":

                False,

        }


    def profile_many(
        self,
        *keys: str,
    ) -> dict[str, dict[str, Any]]:
        """
        Profile multiple dependencies.
        """

        return {

            key:

            self.profile(
                key,
            )

            for key

            in keys

        }


    # ======================================================
    # Resolution Optimization
    # ======================================================

    def warmup(
        self,
    ) -> None:
        """
        Warm up the resolution cache.
        """

        for provider in self._container.provider_names():

            try:

                self.resolve(
                    provider,
                )

            except Exception:

                continue


    def preload(
        self,
        *keys: str,
    ) -> None:
        """
        Preload specific dependencies.
        """

        for key in keys:

            self.resolve(
                key,
            )


    def invalidate(
        self,
        key: str,
    ) -> None:
        """
        Remove an entry from the cache.
        """

        self._cache.pop(
            key,
            None,
        )


    def clear_cache(
        self,
    ) -> None:
        """
        Clear the resolution cache.
        """

        self._cache.clear()

        self._graph_cache.clear()


    # ======================================================
    # Parallel Resolution Planning
    # ======================================================

    def execution_layers(
        self,
    ) -> tuple[
        tuple[str, ...],
        ...
    ]:
        """
        Build dependency execution layers.

        Dependencies within the same layer
        may be resolved in parallel.
        """

        graph = self.dependency_graph()

        indegree = {

            node: 0

            for node

            in graph

        }

        for dependencies in graph.values():

            for dependency in dependencies:

                indegree.setdefault(
                    dependency,
                    0,
                )

                indegree[
                    dependency
                ] += 1

        layers = []

        queue = deque(

            node

            for node, degree

            in indegree.items()

            if degree == 0

        )

        while queue:

            current_layer = tuple(queue)

            layers.append(
                current_layer,
            )

            next_queue = deque()

            while queue:

                node = queue.popleft()

                for dependency in graph.get(
                    node,
                    (),
                ):

                    indegree[
                        dependency
                    ] -= 1

                    if (

                        indegree[
                            dependency
                        ]

                        ==

                        0

                    ):

                        next_queue.append(
                            dependency,
                        )

            queue = next_queue

        return tuple(layers)


    # ======================================================
    # Runtime Metrics
    # ======================================================

    @property
    def cache_size(
        self,
    ) -> int:
        """
        Number of cached resolutions.
        """

        return len(
            self._cache,
        )


    @property
    def graph_size(
        self,
    ) -> int:
        """
        Number of dependency graph nodes.
        """

        return len(
            self.dependency_graph(),
        )


    @property
    def average_resolution_time(
        self,
    ) -> float:
        """
        Average resolution time.
        """

        if (

            self._statistics.resolutions

            ==

            0

        ):

            return 0.0

        return (

            self._metrics.total_resolution_time

            /

            self._statistics.resolutions

        )


    # ======================================================
    # Diagnostics
    # ======================================================

    def diagnostics(
        self,
    ) -> dict[str, Any]:
        """
        Runtime diagnostics.
        """

        return {

            "resolver":

                self.__class__.__name__,

            "version":

                self.VERSION,

            "cache_size":

                self.cache_size,

            "graph_nodes":

                self.graph_size,

            "resolutions":

                self._statistics.resolutions,

            "cache_hits":

                self._statistics.cache_hits,

            "graph_traversals":

                self._statistics.graph_traversals,

            "cycle_checks":

                self._statistics.cycle_checks,

            "failures":

                self._statistics.failures,

            "average_resolution_time":

                self.average_resolution_time,

        }


    # ======================================================
    # Export
    # ======================================================

    def export(
        self,
    ) -> dict[str, Any]:
        """
        Export resolver state.
        """

        return {

            "version":

                self.VERSION,

            "graph":

                self.dependency_graph(),

            "diagnostics":

                self.diagnostics(),

            "statistics":

                self._statistics,

        }
        # ======================================================
    # Runtime Hooks
    # ======================================================

    def before_resolve(
        self,
        key: str,
    ) -> None:
        """
        Executed before dependency resolution.
        """

        return


    def after_resolve(
        self,
        key: str,
        instance: Any,
    ) -> None:
        """
        Executed after dependency resolution.
        """

        return


    def before_cache(
        self,
        key: str,
        instance: Any,
    ) -> None:
        """
        Executed before an instance is cached.
        """

        return


    def after_cache(
        self,
        key: str,
        instance: Any,
    ) -> None:
        """
        Executed after an instance is cached.
        """

        return


    def before_clear(
        self,
    ) -> None:
        """
        Executed before cache clearing.
        """

        return


    def after_clear(
        self,
    ) -> None:
        """
        Executed after cache clearing.
        """

        return


    # ======================================================
    # Health
    # ======================================================

    def check_health(
        self,
    ) -> dict[str, Any]:
        """
        Return resolver health.
        """

        graph = self.dependency_graph()

        healthy = True

        errors: list[str] = []

        try:

            self.validate_graph()

        except Exception as exc:

            healthy = False

            errors.append(
                str(exc),
            )

        return {

            "healthy":

                healthy,

            "cached_entries":

                self.cache_size,

            "graph_nodes":

                len(
                    graph,
                ),

            "errors":

                tuple(errors),

        }


    # ======================================================
    # Inspection
    # ======================================================

    def inspect(
        self,
        key: str,
    ) -> dict[str, Any]:
        """
        Inspect a dependency.
        """

        return {

            "dependency":

                key,

            "dependencies":

                self.dependencies(
                    key,
                ),

            "dependents":

                self.dependents(
                    key,
                ),

            "resolution_plan":

                self.resolution_plan(
                    key,
                ),

            "cached":

                key in self._cache,

        }


    def inspect_graph(
        self,
    ) -> dict[str, Any]:
        """
        Inspect dependency graph.
        """

        graph = self.dependency_graph()

        return {

            "nodes":

                len(
                    graph,
                ),

            "edges":

                sum(

                    len(value)

                    for value

                    in graph.values()

                ),

            "graph":

                graph,

        }


    # ======================================================
    # Maintenance
    # ======================================================

    def reset(
        self,
    ) -> None:
        """
        Reset resolver state.
        """

        self.before_clear()

        self.clear_cache()

        self._statistics = (

            ResolverStatistics()

        )

        self._metrics = (

            ResolverMetrics()

        )

        self.after_clear()


    def shutdown(
        self,
    ) -> None:
        """
        Shutdown resolver.
        """

        self.reset()


    # ======================================================
    # Runtime Information
    # ======================================================

    @property
    def container(
        self,
    ) -> DependencyContainer:
        """
        Return dependency container.
        """

        return self._container


    @property
    def uptime(
        self,
    ) -> float:
        """
        Resolver uptime.
        """

        return (

            time.perf_counter()

            -

            self._metrics.started_at

        )


    @property
    def statistics(
        self,
    ) -> ResolverStatistics:
        """
        Runtime statistics.
        """

        return self._statistics


    @property
    def metrics(
        self,
    ) -> ResolverMetrics:
        """
        Runtime metrics.
        """

        return self._metrics


    # ======================================================
    # Utilities
    # ======================================================

    def refresh(
        self,
    ) -> None:
        """
        Refresh cached dependency graph.
        """

        self._graph_cache = (

            self.dependency_graph()

        )


    def exists(
        self,
        key: str,
    ) -> bool:
        """
        Determine whether a dependency exists.
        """

        return key in self._container


    def is_cached(
        self,
        key: str,
    ) -> bool:
        """
        Determine whether a dependency is cached.
        """

        return key in self._cache


    # ======================================================
    # Context Manager
    # ======================================================

    def __enter__(
        self,
    ) -> Self:
        """
        Enter resolver context.
        """

        self.refresh()

        return self


    def __exit__(
        self,
        exc_type,
        exc,
        traceback,
    ) -> None:
        """
        Exit resolver context.
        """

        self.shutdown()
            # ======================================================
    # Copy Support
    # ======================================================

    def copy(
        self,
    ) -> Self:
        """
        Create a copy of the resolver.
        """

        resolver = self.__class__(
            self._container,
        )

        resolver._cache = deepcopy(
            self._cache,
        )

        resolver._graph_cache = deepcopy(
            self._graph_cache,
        )

        resolver._statistics = deepcopy(
            self._statistics,
        )

        resolver._metrics = deepcopy(
            self._metrics,
        )

        return resolver


    # ======================================================
    # Equality
    # ======================================================

    def __eq__(
        self,
        other: object,
    ) -> bool:
        """
        Compare resolvers.
        """

        if not isinstance(
            other,
            DependencyResolver,
        ):

            return False

        return (

            self._container
            ==
            other._container

            and

            self._cache
            ==
            other._cache

            and

            self._graph_cache
            ==
            other._graph_cache

        )


    # ======================================================
    # Hash Support
    # ======================================================

    def __hash__(
        self,
    ) -> int:
        """
        Object hash.
        """

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
        """
        Developer representation.
        """

        return (

            f"{self.__class__.__name__}("

            f"cache={self.cache_size}, "

            f"graph_nodes={self.graph_size}, "

            f"resolutions={self._statistics.resolutions})"

        )


    # ======================================================
    # Collection API
    # ======================================================

    def __contains__(
        self,
        key: object,
    ) -> bool:
        """
        Determine whether a dependency exists.
        """

        return (

            isinstance(
                key,
                str,
            )

            and

            self.exists(
                key,
            )

        )


    def __getitem__(
        self,
        key: str,
    ) -> Any:
        """
        Resolve dependency.
        """

        return self.resolve(
            key,
        )


    def __iter__(
        self,
    ) -> Iterator[str]:
        """
        Iterate dependency names.
        """

        return iter(

            self._container.provider_names()

        )


    def __len__(
        self,
    ) -> int:
        """
        Number of registered dependencies.
        """

        return len(

            self._container.provider_names()

        )


    def __bool__(
        self,
    ) -> bool:
        """
        Truthiness.
        """

        return len(self) > 0


    # ======================================================
    # Runtime Summary
    # ======================================================

    def full_summary(
        self,
    ) -> dict[str, Any]:
        """
        Enterprise runtime summary.
        """

        return {

            "resolver":

                self.__class__.__name__,

            "version":

                self.VERSION,

            "registered_dependencies":

                len(self),

            "cache_size":

                self.cache_size,

            "graph_nodes":

                self.graph_size,

            "uptime":

                self.uptime,

            "statistics":

                self.statistics,

            "metrics":

                self.metrics,

            "health":

                self.check_health(),

            "diagnostics":

                self.diagnostics(),

            "execution_layers":

                self.execution_layers(),

        }


    # ======================================================
    # Destructor
    # ======================================================

    def __del__(
        self,
    ) -> None:
        """
        Cleanup resources.
        """

        try:

            self.shutdown()

        except Exception:

            pass


# ==========================================================
# Public API
# ==========================================================

__all__ = [

    "DependencyResolver",

    "ResolverStatistics",

    "ResolverMetrics",

]