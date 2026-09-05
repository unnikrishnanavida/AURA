"""Action engine: coordinates preparation and dispatch of an action."""

from __future__ import annotations

from aura_execution.actions.dispatch.action_dispatcher import ActionDispatcher
from aura_execution.actions.dispatch.dispatch_result import DispatchResult
from aura_execution.actions.preparation.action_preparer import ActionPreparer


class ActionEngine:
    """Prepares and dispatches actions, returning a DispatchResult."""

    def __init__(self, dispatcher: ActionDispatcher | None = None, preparer: ActionPreparer | None = None) -> None:
        self.dispatcher = dispatcher or ActionDispatcher()
        self.preparer = preparer or ActionPreparer()

    def execute(self, action: object, inputs: object, context: object) -> DispatchResult:
        try:
            prepared = inputs
            if getattr(action, "inputs", None):
                prepared = self.preparer.prepare(action, getattr(context, "state", {}), inputs)
        except Exception as exc:  # noqa: BLE001 - preparation failure is an execution failure
            return DispatchResult(False, error=f"preparation failed: {exc}")
        return self.dispatcher.dispatch(action, prepared, context)


__all__ = ["ActionEngine"]