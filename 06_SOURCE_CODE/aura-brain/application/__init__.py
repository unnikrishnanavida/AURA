"""Application-layer abstractions for orchestration and composition."""

from .composition_root import CompositionRoot, DependencyContainer
from .dependency_container import DependencyContainer as ServiceContainer
from .orchestrator import ApplicationOrchestrator

__all__ = [
    "ApplicationOrchestrator",
    "CompositionRoot",
    "DependencyContainer",
    "ServiceContainer",
]
