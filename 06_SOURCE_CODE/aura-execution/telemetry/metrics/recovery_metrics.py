class RecoveryMetrics:
    def __init__(self):self.by_strategy={}
    def record(self,strategy,recovered):self.by_strategy.setdefault(strategy,[0,0]);self.by_strategy[strategy][0]+=1;self.by_strategy[strategy][1]+=int(recovered)
