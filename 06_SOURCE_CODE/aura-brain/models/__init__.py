"""Production-oriented model abstractions for AURA Brain."""

from .exceptions import (
    ModelConfigurationError,
    ModelError,
    ModelInitializationError,
    ModelNotFoundError,
    ModelUnavailableError,
)
from .interfaces import ModelLifecycle, ModelProtocol
from .model import Model
from .model_capability import ModelCapability
from .model_config import ModelConfig
from .model_factory import ModelFactory
from .model_health import ModelHealth
from .model_manager import ModelManager
from .model_metrics import ModelMetrics
from .model_registry import ModelRegistry
from .model_state import ModelState, ModelStatus

__all__ = [
    "Model",
    "ModelConfig",
    "ModelCapability",
    "ModelHealth",
    "ModelMetrics",
    "ModelState",
    "ModelStatus",
    "ModelManager",
    "ModelRegistry",
    "ModelFactory",
    "ModelLifecycle",
    "ModelProtocol",
    "ModelError",
    "ModelConfigurationError",
    "ModelInitializationError",
    "ModelNotFoundError",
    "ModelUnavailableError",
]
