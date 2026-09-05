class ActionLedger:
 def __init__(self): self.events=[]
 def record(self,e): self.events.append(e)
