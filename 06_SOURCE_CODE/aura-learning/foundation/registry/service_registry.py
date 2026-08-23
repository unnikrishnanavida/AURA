"""
AURA Framework

Service Registry

Enterprise registry responsible for managing services
across the entire AURA framework.

Managed Services
----------------
• Database Services
• Cache Services
• Network Services
• AI Services
• Storage Services
• Authentication Services
• Runtime Services
• Plugin Services

Every service registered here should inherit from
BaseService.
"""

from __future__ import annotations

from typing import Any
from typing import Type
from typing import TypeVar

from .base_registry import (
    BaseRegistry,
    RegistryEntry,
)

from .exceptions import (
    RegistryValidationError,
)

try:

    from ..base.base_service import BaseService

except ImportError:

    class BaseService:
        """
        Forward declaration.
        """

        ...


T = TypeVar(
    "T",
    bound=BaseService,
)


# ==========================================================
# Service Registry
# ==========================================================

class ServiceRegistry(
    BaseRegistry[
        str,
        T,
    ],
):
    """
    Enterprise Service Registry.

    Manages discovery, lifecycle,
    dependency tracking and monitoring
    of framework services.
    """

    def __init__(
        self,
        **kwargs: Any,
    ) -> None:

        super().__init__(
            **kwargs,
        )

        self._running_services: set[str] = set()

        self._stopped_services: set[str] = set()

        self._failed_services: set[str] = set()

        self._service_groups: dict[
            str,
            set[str],
        ] = {}

    # ======================================================
    # Validation
    # ======================================================

    def validate(
        self,
        key: str,
        value: T,
    ) -> None:
        """
        Validate a service.
        """

        if not isinstance(
            value,
            BaseService,
        ):

            raise RegistryValidationError(

                f"{key!r} "

                "must inherit "

                "BaseService."

            )

    # ======================================================
    # Registration
    # ======================================================

    def register_service(
        self,
        service: T,
        *,
        namespace: str = "services",
        group: str = "default",
    ) -> RegistryEntry[T]:
        """
        Register a framework service.
        """

        entry = self.register(

            key=service.name,

            value=service,

            namespace=namespace,

        )

        self._service_groups.setdefault(

            group,

            set(),

        ).add(

            service.name,

        )

        return entry

    # ======================================================
    # Lookup
    # ======================================================

    def service(
        self,
        name: str,
    ) -> T:
        """
        Return a service.
        """

        return self.require(
            name,
        )

    def services(
        self,
    ) -> tuple[T, ...]:
        """
        Return every registered service.
        """

        return self.values()

    # ======================================================
    # Type Lookup
    # ======================================================

    def service_by_type(
        self,
        service_type: Type[T],
    ) -> T | None:
        """
        Return first matching service.
        """

        for service in self.values():

            if isinstance(

                service,

                service_type,

            ):

                return service

        return None

    def services_by_type(
        self,
        service_type: Type[T],
    ) -> tuple[T, ...]:
        """
        Return all matching services.
        """

        return tuple(

            service

            for service

            in self.values()

            if isinstance(

                service,

                service_type,

            )

        )

    # ======================================================
    # Groups
    # ======================================================

    def groups(
        self,
    ) -> tuple[str, ...]:
        """
        Return all service groups.
        """

        return tuple(

            sorted(

                self._service_groups.keys()

            )

        )

    def services_in_group(
        self,
        group: str,
    ) -> tuple[T, ...]:
        """
        Return services in a group.
        """

        names = self._service_groups.get(

            group,

            set(),

        )

        return tuple(

            self.require(name)

            for name

            in sorted(names)

        )

    def contains_group(
        self,
        group: str,
    ) -> bool:
        """
        Determine whether a group exists.
        """

        return group in self._service_groups
        # ======================================================
    # Service Lifecycle
    # ======================================================

    def start_service(
        self,
        name: str,
    ) -> T:
        """
        Start a registered service.
        """

        service = self.require(
            name,
        )

        if name in self._running_services:

            return service

        try:

            self.before_start(
                service,
            )

            if hasattr(
                service,
                "start",
            ):

                service.start()

            self._running_services.add(
                name,
            )

            self._stopped_services.discard(
                name,
            )

            self._failed_services.discard(
                name,
            )

            self.after_start(
                service,
            )

            return service

        except Exception:

            self._failed_services.add(
                name,
            )

            raise


    def stop_service(
        self,
        name: str,
    ) -> T:
        """
        Stop a registered service.
        """

        service = self.require(
            name,
        )

        if name in self._stopped_services:

            return service

        try:

            self.before_stop(
                service,
            )

            if hasattr(
                service,
                "stop",
            ):

                service.stop()

            self._stopped_services.add(
                name,
            )

            self._running_services.discard(
                name,
            )

            self.after_stop(
                service,
            )

            return service

        except Exception:

            self._failed_services.add(
                name,
            )

            raise


    def restart_service(
        self,
        name: str,
    ) -> T:
        """
        Restart a service.
        """

        self.stop_service(
            name,
        )

        return self.start_service(
            name,
        )


    # ======================================================
    # Bulk Lifecycle
    # ======================================================

    def start_all(
        self,
    ) -> None:
        """
        Start every registered service.
        """

        for name in self.keys():

            self.start_service(
                name,
            )


    def stop_all(
        self,
    ) -> None:
        """
        Stop every registered service.
        """

        for name in reversed(
            self.keys(),
        ):

            self.stop_service(
                name,
            )


    def restart_all(
        self,
    ) -> None:
        """
        Restart every registered service.
        """

        self.stop_all()

        self.start_all()


    # ======================================================
    # Runtime Status
    # ======================================================

    def running_services(
        self,
    ) -> tuple[T, ...]:
        """
        Return every running service.
        """

        return tuple(

            self.require(
                name,
            )

            for name

            in sorted(
                self._running_services
            )

        )


    def stopped_services(
        self,
    ) -> tuple[T, ...]:
        """
        Return every stopped service.
        """

        return tuple(

            self.require(
                name,
            )

            for name

            in sorted(
                self._stopped_services
            )

        )


    def failed_services(
        self,
    ) -> tuple[T, ...]:
        """
        Return every failed service.
        """

        return tuple(

            self.require(
                name,
            )

            for name

            in sorted(
                self._failed_services
            )

        )


    def is_running(
        self,
        name: str,
    ) -> bool:
        """
        Determine whether a service
        is running.
        """

        return (
            name
            in
            self._running_services
        )


    def is_failed(
        self,
        name: str,
    ) -> bool:
        """
        Determine whether a service
        has failed.
        """

        return (
            name
            in
            self._failed_services
        )


    # ======================================================
    # Removal
    # ======================================================

    def unregister_service(
        self,
        name: str,
    ) -> RegistryEntry[T]:
        """
        Remove a service.
        """

        self._running_services.discard(
            name,
        )

        self._stopped_services.discard(
            name,
        )

        self._failed_services.discard(
            name,
        )

        for services in self._service_groups.values():

            services.discard(
                name,
            )

        return self.remove(
            name,
        )


    # ======================================================
    # Statistics
    # ======================================================

    @property
    def running_count(
        self,
    ) -> int:
        """
        Return running service count.
        """

        return len(
            self._running_services
        )


    @property
    def stopped_count(
        self,
    ) -> int:
        """
        Return stopped service count.
        """

        return len(
            self._stopped_services
        )


    @property
    def failed_count(
        self,
    ) -> int:
        """
        Return failed service count.
        """

        return len(
            self._failed_services
        )
        # ======================================================
    # Dependency Lifecycle
    # ======================================================

    def start_dependency_tree(
        self,
        service_name: str,
    ) -> None:
        """
        Start a service together with all of its
        registered dependencies.
        """

        visited: set[str] = set()

        def _start(name: str) -> None:

            if name in visited:
                return

            visited.add(name)

            for dependency in self.dependencies(name):

                _start(dependency)

            self.start_service(name)

        _start(service_name)


    def stop_dependency_tree(
        self,
        service_name: str,
    ) -> None:
        """
        Stop a service together with all
        dependent services.
        """

        visited: set[str] = set()

        def _stop(name: str) -> None:

            if name in visited:
                return

            visited.add(name)

            for dependent in self.dependents(name):

                _stop(dependent)

            self.stop_service(name)

        _stop(service_name)


    # ======================================================
    # Health Monitoring
    # ======================================================

    def healthy_services(
        self,
    ) -> tuple[T, ...]:
        """
        Return all healthy services.
        """

        healthy: list[T] = []

        for service in self.values():

            if not hasattr(
                service,
                "health",
            ):
                continue

            try:

                if service.health():

                    healthy.append(
                        service,
                    )

            except Exception:

                continue

        return tuple(healthy)


    def unhealthy_services(
        self,
    ) -> tuple[T, ...]:
        """
        Return all unhealthy services.
        """

        unhealthy: list[T] = []

        for service in self.values():

            if not hasattr(
                service,
                "health",
            ):
                continue

            try:

                if not service.health():

                    unhealthy.append(
                        service,
                    )

            except Exception:

                unhealthy.append(
                    service,
                )

        return tuple(unhealthy)


    def health_report(
        self,
    ) -> dict[str, Any]:
        """
        Return a runtime health report.
        """

        return {

            "total": self.size,

            "running": self.running_count,

            "stopped": self.stopped_count,

            "failed": self.failed_count,

            "healthy": len(
                self.healthy_services(),
            ),

            "unhealthy": len(
                self.unhealthy_services(),
            ),

        }


    # ======================================================
    # Diagnostics
    # ======================================================

    def diagnostics(
        self,
    ) -> dict[str, Any]:
        """
        Return runtime diagnostics.
        """

        diagnostics = super().diagnostics()

        diagnostics.update(

            {

                "running_services":
                    self.running_count,

                "stopped_services":
                    self.stopped_count,

                "failed_services":
                    self.failed_count,

                "service_groups":
                    len(
                        self._service_groups
                    ),

                "service_types":

                    len(

                        {

                            type(service)

                            for service

                            in self.values()

                        }

                    ),

            }

        )

        return diagnostics


    # ======================================================
    # Search Helpers
    # ======================================================

    def search_services(
        self,
        pattern: str,
    ) -> tuple[T, ...]:
        """
        Search services by name.
        """

        return tuple(

            self.search(
                pattern,
            ).values()

        )


    def services_with_tag(
        self,
        tag: str,
    ) -> tuple[T, ...]:
        """
        Return every tagged service.
        """

        return tuple(

            self.filter_tags(
                tag,
            ).values()

        )


    def services_in_namespace(
        self,
        namespace: str,
    ) -> tuple[T, ...]:
        """
        Return services inside a namespace.
        """

        return tuple(

            self.namespace(
                namespace,
            ).values()

        )


    # ======================================================
    # Runtime Summary
    # ======================================================

    def summary(
        self,
    ) -> dict[str, Any]:
        """
        Return runtime summary.
        """

        summary = super().summary()

        summary.update(

            {

                "running":
                    self.running_count,

                "stopped":
                    self.stopped_count,

                "failed":
                    self.failed_count,

                "healthy":

                    len(

                        self.healthy_services()

                    ),

                "groups":

                    len(

                        self._service_groups

                    ),

            }

        )

        return summary
        # ======================================================
    # Metrics
    # ======================================================

    @property
    def active_services(
        self,
    ) -> int:
        """
        Return the number of active services.
        """

        return self.running_count


    @property
    def inactive_services(
        self,
    ) -> int:
        """
        Return the number of inactive services.
        """

        return self.size - self.running_count


    @property
    def service_types(
        self,
    ) -> tuple[type, ...]:
        """
        Return every unique service type.
        """

        return tuple(

            sorted(

                {

                    type(service)

                    for service

                    in self.values()

                },

                key=lambda cls: cls.__name__,

            )

        )


    def metrics(
        self,
    ) -> dict[str, Any]:
        """
        Return runtime metrics.
        """

        return {

            "total_services":
                self.size,

            "running_services":
                self.running_count,

            "stopped_services":
                self.stopped_count,

            "failed_services":
                self.failed_count,

            "active_services":
                self.active_services,

            "inactive_services":
                self.inactive_services,

            "unique_service_types":

                len(
                    self.service_types
                ),

            "groups":

                len(
                    self._service_groups
                ),

            "namespaces":

                len(
                    self.namespaces()
                ),

            "uptime":

                self.uptime(),

        }


    # ======================================================
    # Snapshot Operations
    # ======================================================

    def create_service_snapshot(
        self,
    ):
        """
        Create a snapshot of the registry.
        """

        return self.create_snapshot()


    def restore_service_snapshot(
        self,
        snapshot,
    ) -> None:
        """
        Restore a previously created snapshot.
        """

        self.restore_snapshot(
            snapshot,
        )


    # ======================================================
    # Export
    # ======================================================

    def export_services(
        self,
    ) -> dict[str, Any]:
        """
        Export all registered services.
        """

        export: dict[str, Any] = {}

        for name, service in self.items():

            export[name] = {

                "type":

                    type(
                        service
                    ).__name__,

                "running":

                    self.is_running(
                        name
                    ),

                "failed":

                    self.is_failed(
                        name
                    ),

                "groups":

                    [

                        group

                        for group, services

                        in self._service_groups.items()

                        if name in services

                    ],

            }

        return export


    # ======================================================
    # Validation
    # ======================================================

    def validate_services(
        self,
    ) -> bool:
        """
        Validate every registered service.
        """

        for service in self.values():

            self.validate(

                service.name,

                service,

            )

        return True


    # ======================================================
    # Lifecycle Hooks
    # ======================================================

    def before_register(
        self,
        entry: RegistryEntry[T],
    ) -> None:
        """
        Executed before service registration.
        """

        return


    def after_register(
        self,
        entry: RegistryEntry[T],
    ) -> None:
        """
        Executed after service registration.
        """

        return


    def before_remove(
        self,
        entry: RegistryEntry[T],
    ) -> None:
        """
        Executed before service removal.
        """

        return


    def after_remove(
        self,
        entry: RegistryEntry[T],
    ) -> None:
        """
        Executed after service removal.
        """

        return


    def before_start(
        self,
        service: T,
    ) -> None:
        """
        Executed before service startup.
        """

        return


    def after_start(
        self,
        service: T,
    ) -> None:
        """
        Executed after service startup.
        """

        return


    def before_stop(
        self,
        service: T,
    ) -> None:
        """
        Executed before service shutdown.
        """

        return


    def after_stop(
        self,
        service: T,
    ) -> None:
        """
        Executed after service shutdown.
        """

        return


    # ======================================================
    # Runtime Helpers
    # ======================================================

    def service_names(
        self,
    ) -> tuple[str, ...]:
        """
        Return every registered service name.
        """

        return self.keys()


    def running_service_names(
        self,
    ) -> tuple[str, ...]:
        """
        Return names of all running services.
        """

        return tuple(

            sorted(
                self._running_services
            )

        )


    def failed_service_names(
        self,
    ) -> tuple[str, ...]:
        """
        Return names of all failed services.
        """

        return tuple(

            sorted(
                self._failed_services
            )

        )
        # ======================================================
    # Context Manager
    # ======================================================

    def __enter__(
        self,
    ) -> Self:
        """
        Enter the registry context.

        Automatically starts all registered services.
        """

        self.start_all()

        return self


    def __exit__(
        self,
        exc_type,
        exc,
        traceback,
    ) -> None:
        """
        Exit the registry context.

        Gracefully stops every service.
        """

        self.stop_all()


    # ======================================================
    # Copy Support
    # ======================================================

    def copy(
        self,
    ) -> Self:
        """
        Create a deep copy of the registry.
        """

        registry = self.__class__()

        for entry in self.entries():

            registry.register(

                key=entry.key,

                value=deepcopy(
                    entry.value,
                ),

                namespace=entry.namespace,

                tags=set(
                    entry.tags,
                ),

                metadata=deepcopy(
                    entry.metadata,
                ),

            )

            if self.is_running(
                entry.key,
            ):

                registry.start_service(
                    entry.key,
                )

        return registry


    # ======================================================
    # Equality
    # ======================================================

    def __eq__(
        self,
        other: object,
    ) -> bool:
        """
        Compare registries.
        """

        if not isinstance(
            other,
            ServiceRegistry,
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

            and

            self._running_services
            ==
            other._running_services

            and

            self._failed_services
            ==
            other._failed_services

        )


    def __hash__(
        self,
    ) -> int:
        """
        Return registry hash.
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

            f"services={self.size}, "

            f"running={self.running_count}, "

            f"failed={self.failed_count})"

        )


    # ======================================================
    # Maintenance
    # ======================================================

    def shutdown(
        self,
    ) -> None:
        """
        Shutdown every registered service.
        """

        self.stop_all()

        super().shutdown()


    def clear_registry(
        self,
    ) -> None:
        """
        Remove every registered service.
        """

        self.stop_all()

        self.clear()

        self._running_services.clear()

        self._stopped_services.clear()

        self._failed_services.clear()

        self._service_groups.clear()


    # ======================================================
    # Group Management
    # ======================================================

    def remove_group(
        self,
        group: str,
    ) -> bool:
        """
        Remove an empty service group.
        """

        services = self._service_groups.get(
            group,
        )

        if services is None:

            return False

        if services:

            return False

        del self._service_groups[
            group
        ]

        return True


    def clear_groups(
        self,
    ) -> None:
        """
        Remove every service group.
        """

        self._service_groups.clear()


    # ======================================================
    # Magic Methods
    # ======================================================

    def __getitem__(
        self,
        name: str,
    ) -> T:
        """
        Retrieve a service.
        """

        return self.service(
            name,
        )


    def __setitem__(
        self,
        name: str,
        service: T,
    ) -> None:
        """
        Register a service.
        """

        self.register_service(
            service,
        )


    def __delitem__(
        self,
        name: str,
    ) -> None:
        """
        Remove a service.
        """

        self.unregister_service(
            name,
        )


    def __bool__(
        self,
    ) -> bool:
        """
        Determine whether the registry
        contains services.
        """

        return not self.is_empty()


    # ======================================================
    # Runtime Summary
    # ======================================================

    def full_summary(
        self,
    ) -> dict[str, Any]:
        """
        Return a complete runtime summary.
        """

        return {

            "registry":
                self.__class__.__name__,

            "services":
                self.size,

            "running":
                self.running_count,

            "stopped":
                self.stopped_count,

            "failed":
                self.failed_count,

            "healthy":

                len(
                    self.healthy_services()
                ),

            "unhealthy":

                len(
                    self.unhealthy_services()
                ),

            "groups":

                len(
                    self._service_groups
                ),

            "statistics":

                self.statistics(),

            "metrics":

                self.metrics(),

            "diagnostics":

                self.diagnostics(),

        }


# ==========================================================
# Public Exports
# ==========================================================

__all__ = [

    "ServiceRegistry",

]