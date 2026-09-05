class CompensationStack:
 def __init__(self):self.steps=[]
 def push(self,fn):self.steps.append(fn)
 def unwind(self):
  out=[]
  while self.steps:out.append(self.steps.pop()())
  return out
