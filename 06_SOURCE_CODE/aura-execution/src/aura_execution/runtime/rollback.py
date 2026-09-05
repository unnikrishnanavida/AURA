"""Rollback and compensation for aura-execution.

Reversible actions record an undo lambda; on failure (or rollback demand) the
rollback coordinator restores the prior state. Irreversible actions must be
compensated by explicit compensation actions registered ahead of execution —
never invented after the fact.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

UndoFn = Callable[[dict[str, Any]], dict[str, Any]]


@dataclass
class RollbackOutcome:
    ok: bool
    rolled_back: list[str] = field(default_factory=list)
    failures: list[str] = field(default_factory=list)

    @property
    def success(self) -> bool:
        return self.ok


class RollbackCoordinator:
    """Restores prior state from registered undo callbacks, LIFO order."""

    def __init__(self) -> None:
        self._undo: dict[str, UndoFn] = {}

    def register_undo(self, action_id: str, undo: UndoFn) -> None:
        self._undo[action_id] = undo

    def rollback(self, state: dict[str, Any], *, action_ids: list[str] | None = None) -> RollbackOutcome:
        targets = action_ids or list(self._undo)
        restored: list[str] = []
        failures: list[str] = []
        current = dict(state)
        for action_id in reversed(targets):
            undo = self._undo.get(action_id)
            if undo is None:
                continue
            try:
                current = undo(current)
                restored.append(action_id)
            except Exception as exc:  # noqa: BLE001 - continue rolling others back
                failures.append(f"{action_id}: {exc}")
        return RollbackOutcome(ok=not failures, rolled_back=restored, failures=failures)


@dataclass
class CompensationAction:
    """An explicit compensation registered ahead of a side-effecting action."""

    action_id: str
    compensate: Callable[[dict[str, Any]], None]


class CompensationRegistry:
    """Stores explicit compensation actions; never invents them."""

    def __init__(self) -> None:
        self._actions: dict[str, CompensationAction] = {}

    def register(self, action: CompensationAction) -> None:
        self._actions[action.action_id] = action

    def compensate(self, action_id: str, state: dict[str, Any]) -> None:
        action = self._actions.get(action_id)
        if action is None:
            raise KeyError(f"no compensation registered for {action_id}")
        action.compensate(state)

    def has(self, action_id: str) -> bool:
        return action_id in self._actions


__all__ = ["CompensationAction", "CompensationRegistry", "RollbackCoordinator", "RollbackOutcome", "UndoFn"]