"""Chat model adapter."""

from __future__ import annotations

from ..model import Model
from ..model_capability import ModelCapability
from ..model_config import ModelConfig
from ..model_health import ModelHealth
from ..model_state import ModelStatus


class ChatModel(Model):
    """Adapter for chat-oriented language models."""

    name = "chat"

    def __init__(self, config: ModelConfig | None = None) -> None:
        super().__init__(config)

    def initialize(self) -> None:
        self.set_state(ModelStatus.INITIALIZING)
        self.register_capability(ModelCapability(name="chat", description="Conversational generation"))
        self.set_state(ModelStatus.READY)

    def shutdown(self) -> None:
        self.set_state(ModelStatus.SHUTDOWN)

    def health_check(self) -> ModelHealth:
        return ModelHealth(healthy=self.is_ready(), message="Chat model ready", status=self.state.status)
