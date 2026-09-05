class SyncQueue:
 def __init__(self):self.items=[]
 def enqueue(self,x):self.items.append(x)
 def drain(self):x,self.items=self.items,[];return x
