"""Vision model adapter."""

from __future__ import annotations

from ..model import Model
from ..model_capability import ModelCapability
from ..model_config import ModelConfig
from ..model_health import ModelHealth
from ..model_state import ModelStatus


class VisionModel(Model):
    """Adapter for vision-oriented models."""

    name = "vision"

    def __init__(self, config: ModelConfig | None = None) -> None:
        super().__init__(config)

    def initialize(self) -> None:
        self.set_state(ModelStatus.INITIALIZING)
        self.register_capability(ModelCapability(name="vision", description="Image and video understanding"))
        self.set_state(ModelStatus.READY)

    def shutdown(self) -> None:
        self.set_state(ModelStatus.SHUTDOWN)

    def health_check(self) -> ModelHealth:
        return ModelHealth(healthy=self.is_ready(), message="Vision model ready", status=self.state.status)
