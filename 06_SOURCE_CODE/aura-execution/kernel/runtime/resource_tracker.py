class ResourceTracker:
    def __init__(self):self.used={}
    def acquire(self,name,amount=1):self.used[name]=self.used.get(name,0)+amount
    def release(self,name,amount=1):self.used[name]=max(0,self.used.get(name,0)-amount)
