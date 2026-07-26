"""Composition root for wiring core application services."""

from __future__ import annotations

import logging
from typing import Any

from bus.dispatcher import Dispatcher
from bus.engine import BusEngine
from gateway.router import Router
from gateway.validator import GatewayValidator
from monitoring.engine import MonitoringEngine
from monitoring.manager import MonitoringManager
from plugins.manager import PluginsManager
from plugins.plugin_loader import PluginLoader
from plugins.plugin_registry import PluginRegistry
from plugins.plugin_validator import PluginValidator
from providers.provider_manager import ProviderManager
from providers.provider_registry import ProviderRegistry
from runtime.runtime import Runtime


def compose(container: Any) -> None:
    """Register foundational services into `container`."""

    logger = logging.getLogger("aura")
    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter("[%(asctime)s] %(levelname)s %(name)s: %(message)s")
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    logger.setLevel(logging.INFO)

    container.register_instance("logger", logger)

    config = {}
    try:
        config = container.resolve("config")
    except Exception:
        pass

    worker_count = 4
    if isinstance(config, dict):
        worker_count = int(config.get("workers", worker_count) or worker_count)

    container.register_factory("runtime", lambda c: Runtime(workers=worker_count))
    container.register_factory("runtime_manager", lambda c: c.resolve("runtime").manager)
    container.register_factory("runtime_queue", lambda c: c.resolve("runtime").queue)
    container.register_factory("runtime_executor", lambda c: c.resolve("runtime").executor)

    container.register_factory("bus_engine", lambda c: BusEngine())
    container.register_factory("bus_dispatcher", lambda c: Dispatcher(c.resolve("bus_engine")))

    container.register_factory("gateway_validator", lambda c: GatewayValidator())
    container.register_factory("gateway_router", lambda c: Router(c.resolve("gateway_validator")))

    container.register_factory("monitoring_engine", lambda c: MonitoringEngine())
    container.register_factory("monitoring_manager", lambda c: MonitoringManager(c.resolve("monitoring_engine")))

    container.register_factory("provider_registry", lambda c: ProviderRegistry())
    container.register_factory("provider_manager", lambda c: ProviderManager(c.resolve("provider_registry")))

    container.register_factory("plugin_loader", lambda c: PluginLoader())
    container.register_factory("plugin_registry", lambda c: PluginRegistry())
    container.register_factory("plugin_validator", lambda c: PluginValidator())
    container.register_factory(
        "plugins_manager",
        lambda c: PluginsManager(
            loader=c.resolve("plugin_loader"),
            registry=c.resolve("plugin_registry"),
            validator=c.resolve("plugin_validator"),
        ),
    )

    def _start_runtime() -> None:
        runtime = container.resolve("runtime")
        runtime.start()

    def _initialize_plugins() -> None:
        plugins = container.resolve("plugins_manager")
        plugins.initialize_all()

    def _shutdown_plugins() -> None:
        plugins = container.resolve("plugins_manager")
        plugins.shutdown_all()

    def _shutdown_providers() -> None:
        providers = container.resolve("provider_manager")
        providers.shutdown_all()

    def _shutdown_runtime() -> None:
        runtime = container.resolve("runtime")
        runtime.shutdown()

    container.register_startup(_start_runtime)
    container.register_startup(_initialize_plugins)
    container.register_shutdown(_shutdown_plugins)
    container.register_shutdown(_shutdown_providers)
    container.register_shutdown(_shutdown_runtime)


class CompositionRoot:
    """A lightweight composition registry for application services."""

    def __init__(self) -> None:
        self._items: list[Any] = []

    def register(self, item: Any) -> None:
        self._items.append(item)

    def list(self) -> list[Any]:
        return list(self._items)

    def clear(self) -> None:
        self._items.clear()
