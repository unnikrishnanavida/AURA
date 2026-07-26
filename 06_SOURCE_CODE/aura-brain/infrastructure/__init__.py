"""Infrastructure-layer skeletons for external integrations and adapters."""

from .base import InfrastructureAdapter
from .adapters.ai_provider_adapter import AIProviderAdapter
from .adapters.plugin_adapter import PluginAdapter
from .adapters.storage_adapter import StorageAdapter
from .adapters.distributed_runtime_adapter import DistributedRuntimeAdapter

__all__ = [
    "AIProviderAdapter",
    "DistributedRuntimeAdapter",
    "InfrastructureAdapter",
    "PluginAdapter",
    "StorageAdapter",
]
