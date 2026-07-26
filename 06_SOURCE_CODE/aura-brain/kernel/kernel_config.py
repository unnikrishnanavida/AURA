"""
Kernel Configuration
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class KernelConfig:
    """Kernel configuration."""

    name: str = "AURA"

    version: str = "0.1.0"

    debug: bool = True

    max_workers: int = 4

    heartbeat_interval: int = 5

    watchdog_interval: int = 10

    enable_plugins: bool = True

    enable_scheduler: bool = True

    enable_diagnostics: bool = True

    enable_recovery: bool = True