class PlannerConsensus:
    def choose(self,plans):
        if not plans: return None
        counts={}
        for p in plans: counts[repr(p)]=counts.get(repr(p),0)+1
        winner=max(counts,key=counts.get)
        return next(p for p in plans if repr(p)==winner)
