class StrategyLearner:
    def __init__(self): self.stats={}
    def update(self,strategy,reward):
        total,count=self.stats.get(strategy,(0.0,0))
        self.stats[strategy]=(total+float(reward),count+1)
    def estimate(self,strategy):
        total,count=self.stats.get(strategy,(0.0,0))
        return total/count if count else 0.0
    def best(self): return max(self.stats,key=self.estimate,default=None)
