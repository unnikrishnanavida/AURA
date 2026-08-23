class CapabilityHealth:
    def __init__(self): self.failures={}
    def record_failure(self,name): self.failures[name]=self.failures.get(name,0)+1
    def healthy(self,name): return self.failures.get(name,0)==0
