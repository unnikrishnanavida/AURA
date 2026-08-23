import time
from .dispatch_result import DispatchResult
class ActionDispatcher:
    def dispatch(self,action,inputs,context):
        if action.handler is None:return DispatchResult(False,error="action has no executable handler")
        started=time.monotonic()
        try:
            value=action.handler(inputs,context)
            return DispatchResult(True,value=value)
        except Exception as e:
            return DispatchResult(False,error=str(e))
