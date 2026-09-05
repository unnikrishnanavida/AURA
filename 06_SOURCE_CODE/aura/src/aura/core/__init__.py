"""AURA core.

The system lifecycle and integration foundation: component registration,
dependency resolution, lifecycle management, health/readiness aggregation,
bootstrap, and runtime context. Core orchestrates; it does not own domain
intelligence.
"""

from __future__ import annotations

from aura.core.bootstrap import Bootstrap, bootstrap_aura
from aura.core.container import Container
from aura.core.context import RuntimeContext
from aura.core.health import (
    HealthAggregator,
    HealthReport,
    HealthStatus,
    Readiness,
    ReadinessStatus,
)
from aura.core.lifecycle_manager import LifecycleManager
from aura.core.registry import ComponentRegistry

__all__ = [
    "Bootstrap",
    "ComponentRegistry",
    "Container",
    "HealthAggregator",
    "HealthReport",
    "HealthStatus",
    "LifecycleManager",
    "Readiness",
    "ReadinessStatus",
    "RuntimeContext",
    "bootstrap_aura",
]