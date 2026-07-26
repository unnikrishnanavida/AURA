"""Service provider base for registering kernel-level services.

This module provides a `ServiceProvider` that accepts the DI container
and exposes a `configure` hook. Concrete kernel extensions should
subclass or replace this provider to register additional services.
"""

from __future__ import annotations

from typing import Any


class ServiceProvider:
    def __init__(self, container: Any) -> None:
        self._container = container

    def configure(self) -> None:
        """Configure kernel services into the provided container.

        Default implementation is a no-op and serves as an extension
        point for real providers.
        """
        try:
            # If a `composition_root` registered a logger, log the hook.
            logger = self._container.resolve("logger")
            try:
                logger.info("ServiceProvider.configure() ran")
            except Exception:
                pass
        except Exception:
            # Container may not have logger; that's fine.
            pass
