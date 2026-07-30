"""Kernel runtime orchestrator.

This module exposes a lightweight, testable Kernel class responsible for
coordinating boot, startup, runtime and shutdown phases. It is intentionally
framework-agnostic and only depends on standard library primitives so it is
easy to integrate into different runtime environments.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Optional, Dict, Any

from .kernel_state import KernelState

logger = logging.getLogger(__name__)


@dataclass
class Kernel:
    """Core kernel that manages lifecycle phases.

    Attributes:
        name: Logical name for the kernel instance.
        config: Arbitrary configuration mapping.
        state: Current kernel lifecycle state.
        context: Extension point for runtime context values.
    """

    name: str = "aura-kernel"
    config: Dict[str, Any] = field(default_factory=dict)
    state: KernelState = KernelState.INITIALIZED
    context: Dict[str, Any] = field(default_factory=dict)

    def start(self) -> None:
        """Start the kernel: perform boot, startup and transition to RUNNING."""
        logger.debug("Starting kernel %s", self.name)
        if self.state is not KernelState.INITIALIZED:
            logger.warning("Kernel %s start called in state %s", self.name, self.state)
            return
        # Boot sequence (delegated to boot loaders via context)
        boot = self.context.get("boot")
        if boot:
            logger.debug("Running boot loader for %s", self.name)
            boot.run(self)

        startup = self.context.get("startup")
        if startup:
            logger.debug("Running startup manager for %s", self.name)
            startup.run(self)

        self.state = KernelState.RUNNING
        logger.info("Kernel %s is running", self.name)

    def stop(self) -> None:
        """Stop the kernel and perform graceful shutdown."""
        logger.debug("Stopping kernel %s", self.name)
        if self.state is KernelState.STOPPED:
            logger.warning("Kernel %s already stopped", self.name)
            return
        shutdown = self.context.get("shutdown")
        if shutdown:
            logger.debug("Running shutdown manager for %s", self.name)
            shutdown.run(self)

        self.state = KernelState.STOPPED
        logger.info("Kernel %s stopped", self.name)

    def register(self, key: str, value: Any) -> None:
        """Register a typed object into kernel context for other subsystems."""
        self.context[key] = value

    def resolve(self, key: str) -> Optional[Any]:
        """Resolve a previously registered item from kernel context."""
        return self.context.get(key)

