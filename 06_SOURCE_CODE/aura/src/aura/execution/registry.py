"""Action registry.

Named registry of executable actions keyed by capability. Registry is
injected; there is no hidden global state.
"""

from __future__ import annotations

from aura.execution.models import ActionSpec
from aura.foundation.errors import NotFoundError


class ActionRegistry:
    def __init__(self) -> None:
        self._actions: dict[str, ActionSpec] = {}

    def register(self, spec: ActionSpec) -> None:
        if spec.name in self._actions:
            raise ValueError(f"action already registered: {spec.name}")
        self._actions[spec.name] = spec

    def get(self, name: str) -> ActionSpec:
        if name not in self._actions:
            raise NotFoundError(f"action not registered: {name}")
        return self._actions[name]

    def has(self, name: str) -> bool:
        return name in self._actions

    def names(self) -> list[str]:
        return sorted(self._actions)

    def capabilities(self) -> set[str]:
        return {spec.capability for spec in self._actions.values()}


__all__ = ["ActionRegistry"]