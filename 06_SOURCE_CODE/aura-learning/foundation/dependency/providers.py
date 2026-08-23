"""
AURA Framework

Dependency Providers

Enterprise provider implementations for the Dependency
Injection subsystem.

Responsibilities
----------------
• Singleton Providers
• Transient Providers
• Scoped Providers
• Factory Providers
• Lazy Providers
• Async Providers
"""

from __future__ import annotations

import threading
import time

from abc import ABC
from abc import abstractmethod

from dataclasses import dataclass
from dataclasses import field

from typing import (
    Any,
    Callable,
    Generic,
    TypeVar,
)

from .container import (
    Lifetime,
)

from .exceptions import (
    ProviderError,
)

# ==========================================================
# Generic Types
# ==========================================================

T = TypeVar("T")

# ==========================================================
# Provider Statistics
# ==========================================================

@dataclass(slots=True)
class ProviderStatistics:

    resolutions: int = 0

    creations: int = 0

    cache_hits: int = 0

    failures: int = 0

# ==========================================================
# Provider Metadata
# ==========================================================

@dataclass(slots=True)
class ProviderMetadata:

    created_at: float = field(
        default_factory=time.time,
    )

    last_access: float = 0.0

    tags: set[str] = field(
        default_factory=set,
    )

    description: str = ""

# ==========================================================
# Base Provider
# ==========================================================

class BaseProvider(
    ABC,
    Generic[T],
):
    """
    Base class for every provider.
    """

    def __init__(
        self,
        implementation: Any,
    ) -> None:

        self._implementation = implementation

        self._lock = threading.RLock()

        self._statistics = (
            ProviderStatistics()
        )

        self._metadata = (
            ProviderMetadata()
        )

    @property
    def implementation(
        self,
    ) -> Any:

        return self._implementation

    @property
    def statistics(
        self,
    ) -> ProviderStatistics:

        return self._statistics

    @property
    def metadata(
        self,
    ) -> ProviderMetadata:

        return self._metadata

    @property
    @abstractmethod
    def lifetime(
        self,
    ) -> Lifetime:
        """
        Provider lifetime.
        """

    @abstractmethod
    def resolve(
        self,
    ) -> T:
        """
        Resolve an instance.
        """

    def before_resolve(
        self,
    ) -> None:
        """
        Hook executed before resolution.
        """

        return

    def after_resolve(
        self,
        instance: Any,
    ) -> None:
        """
        Hook executed after resolution.
        """

        return

# ==========================================================
# Singleton Provider
# ==========================================================

class SingletonProvider(
    BaseProvider[T],
):
    """
    Singleton provider.
    """

    def __init__(
        self,
        implementation: Any,
    ) -> None:

        super().__init__(
            implementation,
        )

        self._instance = None

    @property
    def lifetime(
        self,
    ) -> Lifetime:

        return Lifetime.SINGLETON

    def resolve(
        self,
    ) -> T:

        with self._lock:

            self.before_resolve()

            if self._instance is None:

                self._statistics.creations += 1

                implementation = (
                    self._implementation
                )

                if callable(
                    implementation,
                ):

                    self._instance = (
                        implementation()
                    )

                else:

                    self._instance = (
                        implementation
                    )

            else:

                self._statistics.cache_hits += 1

            self._statistics.resolutions += 1

            self._metadata.last_access = (
                time.time()
            )

            self.after_resolve(
                self._instance,
            )

            return self._instance

# ==========================================================
# Transient Provider
# ==========================================================

class TransientProvider(
    BaseProvider[T],
):
    """
    Transient provider.
    """

    @property
    def lifetime(
        self,
    ) -> Lifetime:

        return Lifetime.TRANSIENT

    def resolve(
        self,
    ) -> T:

        self.before_resolve()

        self._statistics.creations += 1

        self._statistics.resolutions += 1

        implementation = self._implementation

        if callable(
            implementation,
        ):

            instance = implementation()

        else:

            instance = implementation

        self._metadata.last_access = (
            time.time()
        )

        self.after_resolve(
            instance,
        )

        return instance
    # ==========================================================
# Scoped Provider
# ==========================================================

class ScopedProvider(
    BaseProvider[T],
):
    """
    Scoped lifetime provider.
    """

    def __init__(
        self,
        implementation: Any,
    ) -> None:

        super().__init__(
            implementation,
        )

        self._instances: dict[
            str,
            T,
        ] = {}

    @property
    def lifetime(
        self,
    ) -> Lifetime:

        return Lifetime.SCOPED

    def resolve(
        self,
        *,
        scope: str = "default",
    ) -> T:

        with self._lock:

            self.before_resolve()

            if scope in self._instances:

                self._statistics.cache_hits += 1

                instance = self._instances[
                    scope
                ]

            else:

                self._statistics.creations += 1

                implementation = (
                    self._implementation
                )

                if callable(
                    implementation,
                ):

                    instance = implementation()

                else:

                    instance = implementation

                self._instances[
                    scope
                ] = instance

            self._statistics.resolutions += 1

            self._metadata.last_access = (
                time.time()
            )

            self.after_resolve(
                instance,
            )

            return instance

    def clear_scope(
        self,
        scope: str,
    ) -> None:

        self._instances.pop(
            scope,
            None,
        )

    def clear(
        self,
    ) -> None:

        self._instances.clear()


# ==========================================================
# Factory Provider
# ==========================================================

class FactoryProvider(
    BaseProvider[T],
):
    """
    Factory provider.
    """

    @property
    def lifetime(
        self,
    ) -> Lifetime:

        return Lifetime.FACTORY

    def resolve(
        self,
        *args: Any,
        **kwargs: Any,
    ) -> T:

        implementation = self._implementation

        if not callable(
            implementation,
        ):

            raise ProviderError(

                "Factory provider "

                "requires a callable."

            )

        self.before_resolve()

        self._statistics.creations += 1

        self._statistics.resolutions += 1

        instance = implementation(
            *args,
            **kwargs,
        )

        self._metadata.last_access = (
            time.time()
        )

        self.after_resolve(
            instance,
        )

        return instance


# ==========================================================
# Lazy Provider
# ==========================================================

class LazyProvider(
    SingletonProvider[T],
):
    """
    Lazily initialized singleton.
    """

    @property
    def lifetime(
        self,
    ) -> Lifetime:

        return Lifetime.SINGLETON

    @property
    def initialized(
        self,
    ) -> bool:

        return self._instance is not None

    def initialize(
        self,
    ) -> T:

        return self.resolve()


# ==========================================================
# Async Provider
# ==========================================================

class AsyncProvider(
    BaseProvider[T],
):
    """
    Asynchronous provider.
    """

    @property
    def lifetime(
        self,
    ) -> Lifetime:

        return Lifetime.TRANSIENT

    async def resolve_async(
        self,
        *args: Any,
        **kwargs: Any,
    ) -> T:

        implementation = self._implementation

        self.before_resolve()

        self._statistics.creations += 1

        self._statistics.resolutions += 1

        if callable(
            implementation,
        ):

            result = implementation(
                *args,
                **kwargs,
            )

            if hasattr(
                result,
                "__await__",
            ):

                result = await result

        else:

            result = implementation

        self._metadata.last_access = (
            time.time()
        )

        self.after_resolve(
            result,
        )

        return result

    def resolve(
        self,
    ) -> T:

        raise ProviderError(

            "Use resolve_async() "

            "for AsyncProvider."

        )


# ==========================================================
# Cached Provider
# ==========================================================

class CachedProvider(
    SingletonProvider[T],
):
    """
    Singleton provider with refresh support.
    """

    def invalidate(
        self,
    ) -> None:

        self._instance = None

    def refresh(
        self,
    ) -> T:

        self.invalidate()

        return self.resolve()
    # ==========================================================
# Composite Provider
# ==========================================================

class CompositeProvider(
    BaseProvider[T],
):
    """
    Composite provider that resolves using
    multiple child providers.
    """

    def __init__(
        self,
        *providers: BaseProvider[T],
    ) -> None:

        super().__init__(
            implementation=None,
        )

        self._providers = list(
            providers,
        )

    @property
    def lifetime(
        self,
    ) -> Lifetime:

        return Lifetime.TRANSIENT

    def add_provider(
        self,
        provider: BaseProvider[T],
    ) -> None:

        self._providers.append(
            provider,
        )

    def remove_provider(
        self,
        provider: BaseProvider[T],
    ) -> None:

        self._providers.remove(
            provider,
        )

    def providers(
        self,
    ) -> tuple[BaseProvider[T], ...]:

        return tuple(
            self._providers,
        )

    def resolve(
        self,
    ) -> tuple[T, ...]:

        self.before_resolve()

        results = tuple(

            provider.resolve()

            for provider

            in self._providers

        )

        self._statistics.resolutions += 1

        self.after_resolve(
            results,
        )

        return results


# ==========================================================
# Conditional Provider
# ==========================================================

class ConditionalProvider(
    BaseProvider[T],
):
    """
    Resolves only when a condition evaluates True.
    """

    def __init__(
        self,
        implementation: Any,
        *,
        condition: Callable[[], bool],
    ) -> None:

        super().__init__(
            implementation,
        )

        self._condition = condition

    @property
    def lifetime(
        self,
    ) -> Lifetime:

        return Lifetime.TRANSIENT

    def resolve(
        self,
    ) -> T:

        if not self._condition():

            raise ProviderError(

                "Provider condition "

                "was not satisfied."

            )

        implementation = (
            self._implementation
        )

        self.before_resolve()

        self._statistics.creations += 1

        self._statistics.resolutions += 1

        if callable(
            implementation,
        ):

            instance = implementation()

        else:

            instance = implementation

        self.after_resolve(
            instance,
        )

        return instance


# ==========================================================
# Delegating Provider
# ==========================================================

class DelegatingProvider(
    BaseProvider[T],
):
    """
    Delegates resolution to another provider.
    """

    def __init__(
        self,
        provider: BaseProvider[T],
    ) -> None:

        super().__init__(
            provider,
        )

        self._provider = provider

    @property
    def lifetime(
        self,
    ) -> Lifetime:

        return self._provider.lifetime

    def resolve(
        self,
        *args: Any,
        **kwargs: Any,
    ) -> T:

        self.before_resolve()

        instance = self._provider.resolve(
            *args,
            **kwargs,
        )

        self._statistics.resolutions += 1

        self.after_resolve(
            instance,
        )

        return instance


# ==========================================================
# Provider Inspection
# ==========================================================

def provider_info(
    provider: BaseProvider[Any],
) -> dict[str, Any]:
    """
    Return provider information.
    """

    return {

        "provider":

            provider.__class__.__name__,

        "lifetime":

            provider.lifetime.name,

        "implementation":

            getattr(

                provider.implementation,

                "__name__",

                str(
                    provider.implementation
                ),

            ),

        "statistics":

            provider.statistics,

        "metadata":

            provider.metadata,

    }


# ==========================================================
# Diagnostics
# ==========================================================

def provider_diagnostics(
    provider: BaseProvider[Any],
) -> dict[str, Any]:
    """
    Return provider diagnostics.
    """

    stats = provider.statistics

    metadata = provider.metadata

    return {

        "provider":

            provider.__class__.__name__,

        "lifetime":

            provider.lifetime.name,

        "created_at":

            metadata.created_at,

        "last_access":

            metadata.last_access,

        "resolutions":

            stats.resolutions,

        "creations":

            stats.creations,

        "cache_hits":

            stats.cache_hits,

        "failures":

            stats.failures,

    }


# ==========================================================
# Export
# ==========================================================

def export_provider(
    provider: BaseProvider[Any],
) -> dict[str, Any]:
    """
    Export provider state.
    """

    return {

        "provider":

            provider_info(
                provider,
            ),

        "diagnostics":

            provider_diagnostics(
                provider,
            ),

    }
# ==========================================================
# Provider Registry
# ==========================================================

class ProviderRegistry:
    """
    Enterprise provider registry.

    Responsible for managing every provider in
    the dependency subsystem.
    """

    def __init__(
        self,
    ) -> None:

        self._providers: dict[
            str,
            BaseProvider[Any],
        ] = {}

        self._lock = threading.RLock()

    # ======================================================
    # Registration
    # ======================================================

    def register(
        self,
        key: str,
        provider: BaseProvider[Any],
    ) -> BaseProvider[Any]:
        """
        Register a provider.
        """

        with self._lock:

            if key in self._providers:

                raise ProviderError(

                    f"Provider "

                    f"'{key}' "

                    "already registered."

                )

            self._providers[
                key
            ] = provider

            return provider


    def unregister(
        self,
        key: str,
    ) -> BaseProvider[Any]:
        """
        Remove a provider.
        """

        try:

            return self._providers.pop(
                key,
            )

        except KeyError as exc:

            raise ProviderError(

                f"Unknown provider "

                f"'{key}'."

            ) from exc


    # ======================================================
    # Lookup
    # ======================================================

    def provider(
        self,
        key: str,
    ) -> BaseProvider[Any]:
        """
        Return provider.
        """

        try:

            return self._providers[
                key
            ]

        except KeyError as exc:

            raise ProviderError(

                f"Provider "

                f"'{key}' "

                "not found."

            ) from exc


    def resolve(
        self,
        key: str,
        *args: Any,
        **kwargs: Any,
    ) -> Any:
        """
        Resolve a provider.
        """

        return self.provider(
            key,
        ).resolve(
            *args,
            **kwargs,
        )


    # ======================================================
    # Search
    # ======================================================

    def search(
        self,
        pattern: str,
    ) -> dict[str, BaseProvider[Any]]:
        """
        Wildcard provider search.
        """

        import fnmatch

        return {

            key: provider

            for key, provider

            in self._providers.items()

            if fnmatch.fnmatch(
                key,
                pattern,
            )

        }


    def providers_by_lifetime(
        self,
        lifetime: Lifetime,
    ) -> tuple[
        BaseProvider[Any],
        ...
    ]:
        """
        Return providers matching a lifetime.
        """

        return tuple(

            provider

            for provider

            in self._providers.values()

            if provider.lifetime
            is lifetime

        )


    # ======================================================
    # Runtime Information
    # ======================================================

    @property
    def size(
        self,
    ) -> int:

        return len(
            self._providers,
        )


    def names(
        self,
    ) -> tuple[str, ...]:

        return tuple(

            sorted(

                self._providers.keys()

            )

        )


    def values(
        self,
    ) -> tuple[
        BaseProvider[Any],
        ...
    ]:

        return tuple(

            self._providers.values()

        )


    def items(
        self,
    ) -> tuple[
        tuple[
            str,
            BaseProvider[Any],
        ],
        ...
    ]:

        return tuple(

            self._providers.items()

        )


    # ======================================================
    # Diagnostics
    # ======================================================

    def diagnostics(
        self,
    ) -> dict[str, Any]:
        """
        Registry diagnostics.
        """

        return {

            "providers":

                self.size,

            "singleton":

                len(

                    self.providers_by_lifetime(

                        Lifetime.SINGLETON,

                    )

                ),

            "transient":

                len(

                    self.providers_by_lifetime(

                        Lifetime.TRANSIENT,

                    )

                ),

            "scoped":

                len(

                    self.providers_by_lifetime(

                        Lifetime.SCOPED,

                    )

                ),

            "factory":

                len(

                    self.providers_by_lifetime(

                        Lifetime.FACTORY,

                    )

                ),

        }


    # ======================================================
    # Export
    # ======================================================

    def export(
        self,
    ) -> dict[str, Any]:
        """
        Export registry state.
        """

        return {

            key:

            export_provider(
                provider,
            )

            for key, provider

            in self._providers.items()

        }


    # ======================================================
    # Maintenance
    # ======================================================

    def clear(
        self,
    ) -> None:
        """
        Remove every provider.
        """

        self._providers.clear()


    def copy(
        self,
    ) -> Self:
        """
        Deep copy registry.
        """

        registry = self.__class__()

        for key, provider in self._providers.items():

            registry.register(

                key,

                deepcopy(
                    provider,
                ),

            )

        return registry


    # ======================================================
    # Collection API
    # ======================================================

    def __contains__(
        self,
        key: object,
    ) -> bool:

        return (

            isinstance(
                key,
                str,
            )

            and

            key
            in
            self._providers

        )


    def __getitem__(
        self,
        key: str,
    ) -> BaseProvider[Any]:

        return self.provider(
            key,
        )


    def __iter__(
        self,
    ) -> Iterator[str]:

        return iter(
            self._providers,
        )


    def __len__(
        self,
    ) -> int:

        return self.size


    def __bool__(
        self,
    ) -> bool:

        return self.size > 0
    # ==========================================================
# Equality
# ==========================================================

def __provider_equals(
    left: BaseProvider[Any],
    right: object,
) -> bool:
    """
    Compare providers.
    """

    if not isinstance(
        right,
        BaseProvider,
    ):

        return False

    return (

        left.lifetime
        ==
        right.lifetime

        and

        left.implementation
        ==
        right.implementation

        and

        left.metadata
        ==
        right.metadata

    )


BaseProvider.__eq__ = __provider_equals


# ==========================================================
# Hash Support
# ==========================================================

def __provider_hash(
    provider: BaseProvider[Any],
) -> int:
    """
    Provider hash.
    """

    return hash(

        (

            provider.__class__.__name__,

            id(provider),

        )

    )


BaseProvider.__hash__ = __provider_hash


# ==========================================================
# Representation
# ==========================================================

def __provider_repr(
    provider: BaseProvider[Any],
) -> str:
    """
    Developer representation.
    """

    return (

        f"{provider.__class__.__name__}("

        f"lifetime={provider.lifetime.name}, "

        f"implementation="

        f"{getattr(provider.implementation,'__name__',provider.implementation)!r})"

    )


BaseProvider.__repr__ = __provider_repr


# ==========================================================
# Runtime Summary
# ==========================================================

def runtime_summary(
    registry: ProviderRegistry,
) -> dict[str, Any]:
    """
    Return complete runtime summary.
    """

    diagnostics = registry.diagnostics()

    return {

        "registry":

            registry.__class__.__name__,

        "providers":

            registry.size,

        "provider_names":

            registry.names(),

        "statistics":

            diagnostics,

        "export":

            registry.export(),

    }


# ==========================================================
# Provider Factory
# ==========================================================

class ProviderFactory:
    """
    Factory responsible for constructing
    provider implementations.
    """

    @staticmethod
    def create(
        implementation: Any,
        *,
        lifetime: Lifetime,
    ) -> BaseProvider[Any]:

        if lifetime is Lifetime.SINGLETON:

            return SingletonProvider(
                implementation,
            )

        if lifetime is Lifetime.TRANSIENT:

            return TransientProvider(
                implementation,
            )

        if lifetime is Lifetime.SCOPED:

            return ScopedProvider(
                implementation,
            )

        if lifetime is Lifetime.FACTORY:

            return FactoryProvider(
                implementation,
            )

        raise ProviderError(

            f"Unsupported lifetime "

            f"'{lifetime}'."

        )


# ==========================================================
# Public API
# ==========================================================

__all__ = [

    # Base

    "BaseProvider",

    "ProviderStatistics",

    "ProviderMetadata",

    # Providers

    "SingletonProvider",

    "TransientProvider",

    "ScopedProvider",

    "FactoryProvider",

    "LazyProvider",

    "AsyncProvider",

    "CachedProvider",

    "CompositeProvider",

    "ConditionalProvider",

    "DelegatingProvider",

    # Registry

    "ProviderRegistry",

    # Factory

    "ProviderFactory",

    # Utilities

    "provider_info",

    "provider_diagnostics",

    "export_provider",

    "runtime_summary",

]