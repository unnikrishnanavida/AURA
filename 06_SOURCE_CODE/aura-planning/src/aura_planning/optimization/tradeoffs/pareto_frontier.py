class ParetoFrontier:
    @staticmethod
    def dominates(a,b): return all(x>=y for x,y in zip(a,b)) and any(x>y for x,y in zip(a,b))
    def compute(self,candidates):
        return tuple(c for i,c in enumerate(candidates) if not any(self.dominates(o,c) for j,o in enumerate(candidates) if i!=j))
