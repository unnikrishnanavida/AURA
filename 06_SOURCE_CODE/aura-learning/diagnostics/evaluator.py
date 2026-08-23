"""diagnostics.evaluator.py: typed C integration surface."""
from __future__ import annotations
from collections.abc import Mapping
from typing import Any
from aura_learning.runtime import LearningRecord, LearningRuntime, Metrics, serialize, validate_payload
MODULE_NAME = 'diagnostics'
MODULE_FILE = 'evaluator.py'
def validate(value: Mapping[str, Any]) -> None:
    validate_payload(value)
def health(runtime: LearningRuntime) -> dict[str, Any]:
    return runtime.health()
def create_runtime() -> LearningRuntime:
    return LearningRuntime()
class ModuleService:
    """Typed service facade for this module."""
    def __init__(self, runtime: LearningRuntime | None = None) -> None:
        self.runtime = runtime or create_runtime()
    def learn(self, key: str, payload: Mapping[str, Any]) -> LearningRecord:
        validate(payload)
        if self.runtime.state.value != 'running':
            self.runtime.start()
        return self.runtime.learn(key, payload)
    def metrics(self) -> Metrics:
        return self.runtime.metrics
    def serialize(self, value: Any) -> str:
        return serialize(value)
__all__ = ['MODULE_NAME', 'MODULE_FILE', 'ModuleService', 'create_runtime', 'health', 'validate']