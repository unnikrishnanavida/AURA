from .dispatch_result import DispatchResult


class ActionDispatcher:
    def dispatch(self, action, inputs, context):
        if action.handler is None:
            return DispatchResult(False, error="action has no executable handler")
        try:
            value = action.handler(inputs, context)
            return DispatchResult(True, value=value)
        except Exception as exc:  # noqa: BLE001 - handler errors are execution failures
            return DispatchResult(False, error=str(exc))
