class StrategyOptimizer:
    def choose(self,strategies):
        return max(strategies,key=lambda s:s.reliability) if strategies else None
