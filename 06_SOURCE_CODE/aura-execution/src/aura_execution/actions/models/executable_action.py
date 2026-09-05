from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class ExecutableAction:
    action_id: str
    name: str
    capability: str
    inputs: dict[str, Any] = field(default_factory=dict)
    preconditions: dict[str, Any] = field(default_factory=dict)
    effects: dict[str, Any] = field(default_factory=dict)
    permissions: tuple[str, ...] = ()
    risk: float = 0.0
    timeout: float = 30.0
    max_retries: int = 0
    reversible: bool = False
    compensation: str | None = None
    handler: Callable[..., Any] | None = None
    undo: Callable[[dict[str, Any]], dict[str, Any]] | None = None
