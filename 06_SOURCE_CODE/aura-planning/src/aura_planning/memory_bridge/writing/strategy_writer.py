class StrategyWriter:
    def __init__(self,store): self.store=store
    def write(self,strategy,score): self.store[strategy]=score
