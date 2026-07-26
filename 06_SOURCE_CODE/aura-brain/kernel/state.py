"""
AURA Brain Engine

Kernel Bootstrap

Responsible for creating and preparing the kernel.
"""

from __future__ import annotations

from .dependency_container import DependencyContainer
from .service_provider import ServiceProvider

from dataclasses import dataclass
from typing import Any


class KernelState:
    """Simple Kernel state enumeration."""

    CREATED = "created"


@dataclass
class KernelInfo:
    description: str = "AURA Kernel"


@dataclass
class KernelVersion:
    version: str = "0.0.0"


@dataclass
class KernelContext:
    state: str
    version: KernelVersion
    info: KernelInfo

import json
import os
from pathlib import Path

try:
    from application import composition_root
except Exception:
    # When executed as a script the package context may differ; try importlib.
    import importlib

    try:
        composition_root = importlib.import_module("application.composition_root")
    except Exception:
        composition_root = None


class Bootstrap:
    """Creates the kernel foundation."""

    def __init__(self) -> None:
        self._container = DependencyContainer()

    @property
    def container(self) -> DependencyContainer:
        return self._container

    def load_configuration(self) -> None:
        """
        Load configuration.

        Future:
        - YAML
        - JSON
        - Environment Variables
        - Secrets
        """
        # Load configuration from a permissive set of sources.
        config: dict[str, object] = {}

        # 1) Optional config.json at workspace root
        try:
            candidate = Path.cwd() / "config.json"
            if candidate.exists():
                text = candidate.read_text(encoding="utf-8")
                try:
                    config.update(json.loads(text))
                except Exception:
                    # ignore parse errors; prefer env vars
                    pass
        except Exception:
            pass

        # 2) Environment variables starting with AURA_
        for k, v in os.environ.items():
            if k.startswith("AURA_"):
                config[k[5:].lower()] = v

        # 3) Minimal defaults
        config.setdefault("env", os.environ.get("AURA_ENV", "development"))

        # Register configuration in the container for consumers
        try:
            self._container.register_instance("config", config)
        except Exception:
            # older container implementations may support register()
            try:
                self._container.register(config)
            except Exception:
                pass

    def create_context(self) -> KernelContext:
        """Create the initial kernel context."""

        return KernelContext(
            state=KernelState.CREATED,
            version=KernelVersion(),
            info=KernelInfo(),
        )

    def configure_services(self) -> None:
        """Register all kernel services."""
        # Wire composition root first (logger, instrumentation, etc.)
        try:
            import importlib

            mod = importlib.import_module("application.composition_root")
            if hasattr(mod, "compose"):
                try:
                    mod.compose(self._container)
                except Exception:
                    pass
        except Exception:
            # best-effort wiring only
            pass

        # Ensure a logger is available for service providers; composition
        # root may have failed to register one depending on import context.
        try:
            self._container.resolve("logger")
        except Exception:
            try:
                import logging

                logger = logging.getLogger("aura")
                logger.setLevel(logging.INFO)
                self._container.register_instance("logger", logger)
            except Exception:
                pass

        ServiceProvider(self._container).configure()

    def bootstrap(self) -> tuple[DependencyContainer, KernelContext]:
        """Bootstrap the kernel."""

        self.load_configuration()

        self.configure_services()
        self._container.run_startup()

        context = self.create_context()

        return self._container, context

    def shutdown(self) -> None:
        """Shut down configured services gracefully."""
        self._container.run_shutdown()