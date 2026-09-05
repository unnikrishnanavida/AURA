import uuid
from ..models.trace_event import TraceEvent
from ..models.trace_record import TraceRecord
class TraceRecorder:
    def __init__(self): self.trace_id=uuid.uuid4().hex; self.events=[]
    def record(self,name,payload=None,level="info"):
        event=TraceEvent(name,payload=payload or {},level=level); self.events.append(event); return event
    def close(self,metadata=None): return TraceRecord(self.trace_id,tuple(self.events),metadata or {})
