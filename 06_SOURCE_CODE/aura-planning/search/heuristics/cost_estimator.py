class CostEstimator:
    def path_cost(self,path): return sum(float(getattr(a,"cost",0)) for a in path)
