class SingleInstanceGuard:
 def __init__(self): self.claimed=False
 def claim(self):
  if self.claimed:return False
  self.claimed=True;return True
