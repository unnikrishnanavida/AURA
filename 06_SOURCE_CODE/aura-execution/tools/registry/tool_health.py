class ToolHealth:
    def __init__(self): self.failures={}
    def record(self,name,success):
        if success:self.failures[name]=max(0,self.failures.get(name,0)-1)
        else:self.failures[name]=self.failures.get(name,0)+1
    def healthy(self,name):return self.failures.get(name,0)<3
