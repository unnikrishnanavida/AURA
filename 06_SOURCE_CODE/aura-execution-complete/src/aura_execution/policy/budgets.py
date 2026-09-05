class ActionBudget:
 def __init__(self,maximum):self.maximum=maximum;self.used=0
 def consume(self):
  if self.used>=self.maximum:raise RuntimeError('action budget exhausted')
  self.used+=1
