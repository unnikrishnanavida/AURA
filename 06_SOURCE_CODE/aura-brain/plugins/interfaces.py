"""Interfaces for the plugins subsystem."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class PluginsProtocol(Protocol):
    """Common runtime-checkable protocol for plugin components."""

    def execute(self, *args: Any, **kwargs: Any) -> Any:
        """Execute an operation."""
        ...
