class StrategyHistory:
    def __init__(self): self.records=[]
    def add(self,strategy,score): self.records.append((strategy,score))
    def best(self): return max(self.records,key=lambda x:x[1],default=None)
