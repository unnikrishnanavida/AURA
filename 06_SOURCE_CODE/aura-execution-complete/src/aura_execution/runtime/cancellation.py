class CancellationToken:
 def __init__(self):self.cancelled=False
 def cancel(self):self.cancelled=True
 def check(self):
  if self.cancelled:raise RuntimeError('execution cancelled')
