class Gauge:
    def __init__(self,value=0.): self.value=float(value)
    def set(self,value): self.value=float(value)
    def get(self): return self.value
