import hashlib,json
class ExecutionLedger:
 def __init__(self):self.events=[];self.head='GENESIS'
 def append(self,event):
  self.head=hashlib.sha256((self.head+json.dumps(event,sort_keys=True,default=str)).encode()).hexdigest();self.events.append({'event':event,'hash':self.head})
