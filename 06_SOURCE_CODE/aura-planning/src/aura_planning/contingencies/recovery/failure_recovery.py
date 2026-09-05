class FailureRecovery:
    def __init__(self, planner): self.planner=planner
    def handle(self, failure, context):
        result=self.planner.recover(failure,context)
        if result is None: raise RuntimeError(f"no recovery strategy for {failure}")
        return result
