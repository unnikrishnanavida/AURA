class UtilityOptimizer:
    def maximize(self,candidates,utility): return max(candidates,key=utility,default=None)
