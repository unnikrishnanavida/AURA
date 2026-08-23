class DispatchStrategy:
    def select(self,action): return "handler" if action.handler else "unavailable"
