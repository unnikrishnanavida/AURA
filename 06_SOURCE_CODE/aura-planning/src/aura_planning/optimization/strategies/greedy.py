class GreedyOptimizer:
    def optimize(self,candidates,score): return sorted(candidates,key=score,reverse=True)
