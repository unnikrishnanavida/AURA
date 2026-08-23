import time
from .events.execution_event import ExecutionEvent
class FlightRecorder:
    def __init__(self,store=None):self.store=store;self.events=[]
    def record(self,execution_id,event,**data):
        item=ExecutionEvent(time.time(),execution_id,event,data);self.events.append(item)
        if self.store:self.store.append(item)
        return item
    def for_execution(self,eid):return [e for e in self.events if e.execution_id==eid]
