class RecoveryPlanner:
    def __init__(self,strategies=()): self.strategies=tuple(strategies)
    def recover(self,failure,context):
        for strategy in self.strategies:
            result=strategy.recover(failure,context)
            if result is not None: return result
        return None
