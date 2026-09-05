class StrategyRouter:
    def __init__(self, strategies=()):
        self.strategies = list(strategies)
    def register(self, strategy):
        if strategy not in self.strategies:
            self.strategies.append(strategy)
    def route(self, request):
        for strategy in self.strategies:
            if strategy.supports(request):
                return strategy
        return None
