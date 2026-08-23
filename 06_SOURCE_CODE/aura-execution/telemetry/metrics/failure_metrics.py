class FailureMetrics:
    def __init__(self):self.counts={}
    def record(self,kind):self.counts[kind]=self.counts.get(kind,0)+1
