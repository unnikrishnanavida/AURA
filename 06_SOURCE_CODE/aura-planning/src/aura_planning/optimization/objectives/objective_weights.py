class ObjectiveWeights:
    def __init__(self,weights): self.weights=dict(weights)
    def normalize(self):
        total=sum(max(0,float(v)) for v in self.weights.values())
        if total==0: raise ValueError("objective weights must have positive mass")
        return {k:max(0,float(v))/total for k,v in self.weights.items()}
