"""Reasoning model adapter."""

from __future__ import annotations

from ..model import Model
from ..model_capability import ModelCapability
from ..model_config import ModelConfig
from ..model_health import ModelHealth
from ..model_state import ModelStatus


class ReasoningModel(Model):
    """Adapter for reasoning-oriented models."""

    name = "reasoning"

    def __init__(self, config: ModelConfig | None = None) -> None:
        super().__init__(config)

    def initialize(self) -> None:
        self.set_state(ModelStatus.INITIALIZING)
        self.register_capability(ModelCapability(name="reasoning", description="Complex reasoning and planning"))
        self.set_state(ModelStatus.READY)

    def shutdown(self) -> None:
        self.set_state(ModelStatus.SHUTDOWN)

    def health_check(self) -> ModelHealth:
        return ModelHealth(healthy=self.is_ready(), message="Reasoning model ready", status=self.state.status)
