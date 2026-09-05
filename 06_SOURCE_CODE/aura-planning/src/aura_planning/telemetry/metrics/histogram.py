class Histogram:
    def __init__(self): self.samples=[]
    def observe(self,value): self.samples.append(float(value))
    def summary(self):
        if not self.samples: return {"count":0}
        values=sorted(self.samples); n=len(values)
        return {"count":n,"min":values[0],"max":values[-1],"mean":sum(values)/n}
