class OfflineQueue:
 def __init__(self): self.items=[]
 def push(self,x): self.items.append(x)
 def drain(self): x,self.items=self.items,[];return x
