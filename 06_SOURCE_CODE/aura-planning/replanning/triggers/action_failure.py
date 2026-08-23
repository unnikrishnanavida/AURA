class ActionFailureTrigger:
    def triggered(self,outcome): return not bool(getattr(outcome,"success",False))
