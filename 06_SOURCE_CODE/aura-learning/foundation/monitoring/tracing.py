"""AURA in-process tracing with nested spans and trace queries."""
from __future__ import annotations
import contextvars,functools,secrets,threading,time
from contextlib import contextmanager
from dataclasses import dataclass,field
from typing import Any
_trace=contextvars.ContextVar("aura_trace",default=None);_span=contextvars.ContextVar("aura_span",default=None)
def generate_id(size=8):return secrets.token_hex(size)
@dataclass
class SpanEvent:
    name:str;timestamp:float=field(default_factory=time.time);attributes:dict[str,Any]=field(default_factory=dict)
    def as_dict(self):return {"name":self.name,"timestamp":self.timestamp,"attributes":dict(self.attributes)}
@dataclass
class Span:
    name:str;trace_id:str;span_id:str;parent_id:str|None=None;started_at:float=field(default_factory=time.time);ended_at:float|None=None;status:str="unset";attributes:dict[str,Any]=field(default_factory=dict);events:list[SpanEvent]=field(default_factory=list);error:dict|None=None
    @property
    def ended(self):return self.ended_at is not None
    @property
    def duration_seconds(self):return None if self.ended_at is None else self.ended_at-self.started_at
    @property
    def duration_ms(self):return None if self.duration_seconds is None else self.duration_seconds*1000
    def set_attribute(self,key,value):self.attributes[str(key)]=value;return self
    def set_attributes(self,values):self.attributes.update(values);return self
    def add_event(self,name,**attributes):self.events.append(SpanEvent(str(name),attributes));return self
    def record_error(self,error):self.status="error";self.error={"type":type(error).__name__,"message":str(error)};return self.add_event("exception",message=str(error),exception_type=type(error).__name__)
    def end(self,status="ok"):
        if not self.ended:self.status=status;self.ended_at=time.time()
        return self
    def as_dict(self):return {"name":self.name,"trace_id":self.trace_id,"span_id":self.span_id,"parent_id":self.parent_id,"started_at":self.started_at,"ended_at":self.ended_at,"duration_ms":self.duration_ms,"status":self.status,"attributes":dict(self.attributes),"events":[e.as_dict() for e in self.events],"error":self.error}
class Tracer:
    def __init__(self,name="aura",max_spans=5000,sample_rate=1):self.name=name;self.max_spans=max(1,int(max_spans));self.sample_rate=float(sample_rate);self._spans=[];self._lock=threading.RLock()
    def should_sample(self):return secrets.randbelow(1000000)<self.sample_rate*1000000
    def start_span(self,name,attributes=None,new_trace=False):
        tid=None if new_trace else _trace.get();tid=tid or generate_id(16);return Span(str(name),tid,generate_id(8),_span.get(),attributes=dict(attributes or {}))
    def record(self,span):
        if not self.should_sample():return
        with self._lock:
            self._spans.append(span)
            if len(self._spans)>self.max_spans:del self._spans[:len(self._spans)-self.max_spans]
    @contextmanager
    def span(self,name,attributes=None,new_trace=False):
        s=self.start_span(name,attributes,new_trace);a=_trace.set(s.trace_id);b=_span.set(s.span_id)
        try:yield s
        except Exception as exc:s.record_error(exc);s.end("error");raise
        else:s.end("ok")
        finally:_span.reset(b);_trace.reset(a);self.record(s)
    def trace(self,name=None,attributes=None):
        def deco(fn):
            @functools.wraps(fn)
            def wrapper(*a,**kw):
                with self.span(name or fn.__qualname__,attributes):return fn(*a,**kw)
            return wrapper
        return deco
    def current_trace_id(self):return _trace.get()
    def current_span_id(self):return _span.get()
    def spans(self):
        with self._lock:return list(self._spans)
    def snapshot(self):return [s.as_dict() for s in self.spans()]
    def find_trace(self,tid):return [s for s in self.spans() if s.trace_id==tid]
    def find_by_name(self,name):return [s for s in self.spans() if s.name==name]
    def clear(self):
        with self._lock:self._spans.clear()
    def health(self):return True

class TraceDomain1:
    """Trace namespace for subsystem 1."""
    def __init__(self,tracer=None):self.tracer=tracer or Tracer();self.prefix="subsystem_1"
    def name(self,key):return f"{self.prefix}.{key}"
    def span(self,key,**kw):return self.tracer.span(self.name(key),**kw)
    def start(self,key,**kw):return self.tracer.start_span(self.name(key),**kw)
    def find(self,key):return self.tracer.find_by_name(self.name(key))
    def names(self):return sorted(set(s.name for s in self.tracer.spans() if s.name.startswith(self.prefix+".")))
    def count(self):return len([s for s in self.tracer.spans() if s.name.startswith(self.prefix+".")])
    def errors(self):return [s for s in self.tracer.spans() if s.name.startswith(self.prefix+".") and s.status=="error"]
    def durations(self):return [s.duration_ms for s in self.tracer.spans() if s.name.startswith(self.prefix+".") and s.duration_ms is not None]
    def average_duration(self):
        v=self.durations();return sum(v)/len(v) if v else 0


class TraceDomain2:
    """Trace namespace for subsystem 2."""
    def __init__(self,tracer=None):self.tracer=tracer or Tracer();self.prefix="subsystem_2"
    def name(self,key):return f"{self.prefix}.{key}"
    def span(self,key,**kw):return self.tracer.span(self.name(key),**kw)
    def start(self,key,**kw):return self.tracer.start_span(self.name(key),**kw)
    def find(self,key):return self.tracer.find_by_name(self.name(key))
    def names(self):return sorted(set(s.name for s in self.tracer.spans() if s.name.startswith(self.prefix+".")))
    def count(self):return len([s for s in self.tracer.spans() if s.name.startswith(self.prefix+".")])
    def errors(self):return [s for s in self.tracer.spans() if s.name.startswith(self.prefix+".") and s.status=="error"]
    def durations(self):return [s.duration_ms for s in self.tracer.spans() if s.name.startswith(self.prefix+".") and s.duration_ms is not None]
    def average_duration(self):
        v=self.durations();return sum(v)/len(v) if v else 0


class TraceDomain3:
    """Trace namespace for subsystem 3."""
    def __init__(self,tracer=None):self.tracer=tracer or Tracer();self.prefix="subsystem_3"
    def name(self,key):return f"{self.prefix}.{key}"
    def span(self,key,**kw):return self.tracer.span(self.name(key),**kw)
    def start(self,key,**kw):return self.tracer.start_span(self.name(key),**kw)
    def find(self,key):return self.tracer.find_by_name(self.name(key))
    def names(self):return sorted(set(s.name for s in self.tracer.spans() if s.name.startswith(self.prefix+".")))
    def count(self):return len([s for s in self.tracer.spans() if s.name.startswith(self.prefix+".")])
    def errors(self):return [s for s in self.tracer.spans() if s.name.startswith(self.prefix+".") and s.status=="error"]
    def durations(self):return [s.duration_ms for s in self.tracer.spans() if s.name.startswith(self.prefix+".") and s.duration_ms is not None]
    def average_duration(self):
        v=self.durations();return sum(v)/len(v) if v else 0


class TraceDomain4:
    """Trace namespace for subsystem 4."""
    def __init__(self,tracer=None):self.tracer=tracer or Tracer();self.prefix="subsystem_4"
    def name(self,key):return f"{self.prefix}.{key}"
    def span(self,key,**kw):return self.tracer.span(self.name(key),**kw)
    def start(self,key,**kw):return self.tracer.start_span(self.name(key),**kw)
    def find(self,key):return self.tracer.find_by_name(self.name(key))
    def names(self):return sorted(set(s.name for s in self.tracer.spans() if s.name.startswith(self.prefix+".")))
    def count(self):return len([s for s in self.tracer.spans() if s.name.startswith(self.prefix+".")])
    def errors(self):return [s for s in self.tracer.spans() if s.name.startswith(self.prefix+".") and s.status=="error"]
    def durations(self):return [s.duration_ms for s in self.tracer.spans() if s.name.startswith(self.prefix+".") and s.duration_ms is not None]
    def average_duration(self):
        v=self.durations();return sum(v)/len(v) if v else 0


class TraceDomain5:
    """Trace namespace for subsystem 5."""
    def __init__(self,tracer=None):self.tracer=tracer or Tracer();self.prefix="subsystem_5"
    def name(self,key):return f"{self.prefix}.{key}"
    def span(self,key,**kw):return self.tracer.span(self.name(key),**kw)
    def start(self,key,**kw):return self.tracer.start_span(self.name(key),**kw)
    def find(self,key):return self.tracer.find_by_name(self.name(key))
    def names(self):return sorted(set(s.name for s in self.tracer.spans() if s.name.startswith(self.prefix+".")))
    def count(self):return len([s for s in self.tracer.spans() if s.name.startswith(self.prefix+".")])
    def errors(self):return [s for s in self.tracer.spans() if s.name.startswith(self.prefix+".") and s.status=="error"]
    def durations(self):return [s.duration_ms for s in self.tracer.spans() if s.name.startswith(self.prefix+".") and s.duration_ms is not None]
    def average_duration(self):
        v=self.durations();return sum(v)/len(v) if v else 0


class TraceDomain6:
    """Trace namespace for subsystem 6."""
    def __init__(self,tracer=None):self.tracer=tracer or Tracer();self.prefix="subsystem_6"
    def name(self,key):return f"{self.prefix}.{key}"
    def span(self,key,**kw):return self.tracer.span(self.name(key),**kw)
    def start(self,key,**kw):return self.tracer.start_span(self.name(key),**kw)
    def find(self,key):return self.tracer.find_by_name(self.name(key))
    def names(self):return sorted(set(s.name for s in self.tracer.spans() if s.name.startswith(self.prefix+".")))
    def count(self):return len([s for s in self.tracer.spans() if s.name.startswith(self.prefix+".")])
    def errors(self):return [s for s in self.tracer.spans() if s.name.startswith(self.prefix+".") and s.status=="error"]
    def durations(self):return [s.duration_ms for s in self.tracer.spans() if s.name.startswith(self.prefix+".") and s.duration_ms is not None]
    def average_duration(self):
        v=self.durations();return sum(v)/len(v) if v else 0


class TraceDomain7:
    """Trace namespace for subsystem 7."""
    def __init__(self,tracer=None):self.tracer=tracer or Tracer();self.prefix="subsystem_7"
    def name(self,key):return f"{self.prefix}.{key}"
    def span(self,key,**kw):return self.tracer.span(self.name(key),**kw)
    def start(self,key,**kw):return self.tracer.start_span(self.name(key),**kw)
    def find(self,key):return self.tracer.find_by_name(self.name(key))
    def names(self):return sorted(set(s.name for s in self.tracer.spans() if s.name.startswith(self.prefix+".")))
    def count(self):return len([s for s in self.tracer.spans() if s.name.startswith(self.prefix+".")])
    def errors(self):return [s for s in self.tracer.spans() if s.name.startswith(self.prefix+".") and s.status=="error"]
    def durations(self):return [s.duration_ms for s in self.tracer.spans() if s.name.startswith(self.prefix+".") and s.duration_ms is not None]
    def average_duration(self):
        v=self.durations();return sum(v)/len(v) if v else 0


class TraceDomain8:
    """Trace namespace for subsystem 8."""
    def __init__(self,tracer=None):self.tracer=tracer or Tracer();self.prefix="subsystem_8"
    def name(self,key):return f"{self.prefix}.{key}"
    def span(self,key,**kw):return self.tracer.span(self.name(key),**kw)
    def start(self,key,**kw):return self.tracer.start_span(self.name(key),**kw)
    def find(self,key):return self.tracer.find_by_name(self.name(key))
    def names(self):return sorted(set(s.name for s in self.tracer.spans() if s.name.startswith(self.prefix+".")))
    def count(self):return len([s for s in self.tracer.spans() if s.name.startswith(self.prefix+".")])
    def errors(self):return [s for s in self.tracer.spans() if s.name.startswith(self.prefix+".") and s.status=="error"]
    def durations(self):return [s.duration_ms for s in self.tracer.spans() if s.name.startswith(self.prefix+".") and s.duration_ms is not None]
    def average_duration(self):
        v=self.durations();return sum(v)/len(v) if v else 0


class TraceDomain9:
    """Trace namespace for subsystem 9."""
    def __init__(self,tracer=None):self.tracer=tracer or Tracer();self.prefix="subsystem_9"
    def name(self,key):return f"{self.prefix}.{key}"
    def span(self,key,**kw):return self.tracer.span(self.name(key),**kw)
    def start(self,key,**kw):return self.tracer.start_span(self.name(key),**kw)
    def find(self,key):return self.tracer.find_by_name(self.name(key))
    def names(self):return sorted(set(s.name for s in self.tracer.spans() if s.name.startswith(self.prefix+".")))
    def count(self):return len([s for s in self.tracer.spans() if s.name.startswith(self.prefix+".")])
    def errors(self):return [s for s in self.tracer.spans() if s.name.startswith(self.prefix+".") and s.status=="error"]
    def durations(self):return [s.duration_ms for s in self.tracer.spans() if s.name.startswith(self.prefix+".") and s.duration_ms is not None]
    def average_duration(self):
        v=self.durations();return sum(v)/len(v) if v else 0


class TraceDomain10:
    """Trace namespace for subsystem 10."""
    def __init__(self,tracer=None):self.tracer=tracer or Tracer();self.prefix="subsystem_10"
    def name(self,key):return f"{self.prefix}.{key}"
    def span(self,key,**kw):return self.tracer.span(self.name(key),**kw)
    def start(self,key,**kw):return self.tracer.start_span(self.name(key),**kw)
    def find(self,key):return self.tracer.find_by_name(self.name(key))
    def names(self):return sorted(set(s.name for s in self.tracer.spans() if s.name.startswith(self.prefix+".")))
    def count(self):return len([s for s in self.tracer.spans() if s.name.startswith(self.prefix+".")])
    def errors(self):return [s for s in self.tracer.spans() if s.name.startswith(self.prefix+".") and s.status=="error"]
    def durations(self):return [s.duration_ms for s in self.tracer.spans() if s.name.startswith(self.prefix+".") and s.duration_ms is not None]
    def average_duration(self):
        v=self.durations();return sum(v)/len(v) if v else 0


class TraceDomain11:
    """Trace namespace for subsystem 11."""
    def __init__(self,tracer=None):self.tracer=tracer or Tracer();self.prefix="subsystem_11"
    def name(self,key):return f"{self.prefix}.{key}"
    def span(self,key,**kw):return self.tracer.span(self.name(key),**kw)
    def start(self,key,**kw):return self.tracer.start_span(self.name(key),**kw)
    def find(self,key):return self.tracer.find_by_name(self.name(key))
    def names(self):return sorted(set(s.name for s in self.tracer.spans() if s.name.startswith(self.prefix+".")))
    def count(self):return len([s for s in self.tracer.spans() if s.name.startswith(self.prefix+".")])
    def errors(self):return [s for s in self.tracer.spans() if s.name.startswith(self.prefix+".") and s.status=="error"]
    def durations(self):return [s.duration_ms for s in self.tracer.spans() if s.name.startswith(self.prefix+".") and s.duration_ms is not None]
    def average_duration(self):
        v=self.durations();return sum(v)/len(v) if v else 0


class TraceDomain12:
    """Trace namespace for subsystem 12."""
    def __init__(self,tracer=None):self.tracer=tracer or Tracer();self.prefix="subsystem_12"
    def name(self,key):return f"{self.prefix}.{key}"
    def span(self,key,**kw):return self.tracer.span(self.name(key),**kw)
    def start(self,key,**kw):return self.tracer.start_span(self.name(key),**kw)
    def find(self,key):return self.tracer.find_by_name(self.name(key))
    def names(self):return sorted(set(s.name for s in self.tracer.spans() if s.name.startswith(self.prefix+".")))
    def count(self):return len([s for s in self.tracer.spans() if s.name.startswith(self.prefix+".")])
    def errors(self):return [s for s in self.tracer.spans() if s.name.startswith(self.prefix+".") and s.status=="error"]
    def durations(self):return [s.duration_ms for s in self.tracer.spans() if s.name.startswith(self.prefix+".") and s.duration_ms is not None]
    def average_duration(self):
        v=self.durations();return sum(v)/len(v) if v else 0


class TraceDomain13:
    """Trace namespace for subsystem 13."""
    def __init__(self,tracer=None):self.tracer=tracer or Tracer();self.prefix="subsystem_13"
    def name(self,key):return f"{self.prefix}.{key}"
    def span(self,key,**kw):return self.tracer.span(self.name(key),**kw)
    def start(self,key,**kw):return self.tracer.start_span(self.name(key),**kw)
    def find(self,key):return self.tracer.find_by_name(self.name(key))
    def names(self):return sorted(set(s.name for s in self.tracer.spans() if s.name.startswith(self.prefix+".")))
    def count(self):return len([s for s in self.tracer.spans() if s.name.startswith(self.prefix+".")])
    def errors(self):return [s for s in self.tracer.spans() if s.name.startswith(self.prefix+".") and s.status=="error"]
    def durations(self):return [s.duration_ms for s in self.tracer.spans() if s.name.startswith(self.prefix+".") and s.duration_ms is not None]
    def average_duration(self):
        v=self.durations();return sum(v)/len(v) if v else 0


class TraceDomain14:
    """Trace namespace for subsystem 14."""
    def __init__(self,tracer=None):self.tracer=tracer or Tracer();self.prefix="subsystem_14"
    def name(self,key):return f"{self.prefix}.{key}"
    def span(self,key,**kw):return self.tracer.span(self.name(key),**kw)
    def start(self,key,**kw):return self.tracer.start_span(self.name(key),**kw)
    def find(self,key):return self.tracer.find_by_name(self.name(key))
    def names(self):return sorted(set(s.name for s in self.tracer.spans() if s.name.startswith(self.prefix+".")))
    def count(self):return len([s for s in self.tracer.spans() if s.name.startswith(self.prefix+".")])
    def errors(self):return [s for s in self.tracer.spans() if s.name.startswith(self.prefix+".") and s.status=="error"]
    def durations(self):return [s.duration_ms for s in self.tracer.spans() if s.name.startswith(self.prefix+".") and s.duration_ms is not None]
    def average_duration(self):
        v=self.durations();return sum(v)/len(v) if v else 0


class TraceDomain15:
    """Trace namespace for subsystem 15."""
    def __init__(self,tracer=None):self.tracer=tracer or Tracer();self.prefix="subsystem_15"
    def name(self,key):return f"{self.prefix}.{key}"
    def span(self,key,**kw):return self.tracer.span(self.name(key),**kw)
    def start(self,key,**kw):return self.tracer.start_span(self.name(key),**kw)
    def find(self,key):return self.tracer.find_by_name(self.name(key))
    def names(self):return sorted(set(s.name for s in self.tracer.spans() if s.name.startswith(self.prefix+".")))
    def count(self):return len([s for s in self.tracer.spans() if s.name.startswith(self.prefix+".")])
    def errors(self):return [s for s in self.tracer.spans() if s.name.startswith(self.prefix+".") and s.status=="error"]
    def durations(self):return [s.duration_ms for s in self.tracer.spans() if s.name.startswith(self.prefix+".") and s.duration_ms is not None]
    def average_duration(self):
        v=self.durations();return sum(v)/len(v) if v else 0


class TraceDomain16:
    """Trace namespace for subsystem 16."""
    def __init__(self,tracer=None):self.tracer=tracer or Tracer();self.prefix="subsystem_16"
    def name(self,key):return f"{self.prefix}.{key}"
    def span(self,key,**kw):return self.tracer.span(self.name(key),**kw)
    def start(self,key,**kw):return self.tracer.start_span(self.name(key),**kw)
    def find(self,key):return self.tracer.find_by_name(self.name(key))
    def names(self):return sorted(set(s.name for s in self.tracer.spans() if s.name.startswith(self.prefix+".")))
    def count(self):return len([s for s in self.tracer.spans() if s.name.startswith(self.prefix+".")])
    def errors(self):return [s for s in self.tracer.spans() if s.name.startswith(self.prefix+".") and s.status=="error"]
    def durations(self):return [s.duration_ms for s in self.tracer.spans() if s.name.startswith(self.prefix+".") and s.duration_ms is not None]
    def average_duration(self):
        v=self.durations();return sum(v)/len(v) if v else 0


class TraceDomain17:
    """Trace namespace for subsystem 17."""
    def __init__(self,tracer=None):self.tracer=tracer or Tracer();self.prefix="subsystem_17"
    def name(self,key):return f"{self.prefix}.{key}"
    def span(self,key,**kw):return self.tracer.span(self.name(key),**kw)
    def start(self,key,**kw):return self.tracer.start_span(self.name(key),**kw)
    def find(self,key):return self.tracer.find_by_name(self.name(key))
    def names(self):return sorted(set(s.name for s in self.tracer.spans() if s.name.startswith(self.prefix+".")))
    def count(self):return len([s for s in self.tracer.spans() if s.name.startswith(self.prefix+".")])
    def errors(self):return [s for s in self.tracer.spans() if s.name.startswith(self.prefix+".") and s.status=="error"]
    def durations(self):return [s.duration_ms for s in self.tracer.spans() if s.name.startswith(self.prefix+".") and s.duration_ms is not None]
    def average_duration(self):
        v=self.durations();return sum(v)/len(v) if v else 0


class TraceDomain18:
    """Trace namespace for subsystem 18."""
    def __init__(self,tracer=None):self.tracer=tracer or Tracer();self.prefix="subsystem_18"
    def name(self,key):return f"{self.prefix}.{key}"
    def span(self,key,**kw):return self.tracer.span(self.name(key),**kw)
    def start(self,key,**kw):return self.tracer.start_span(self.name(key),**kw)
    def find(self,key):return self.tracer.find_by_name(self.name(key))
    def names(self):return sorted(set(s.name for s in self.tracer.spans() if s.name.startswith(self.prefix+".")))
    def count(self):return len([s for s in self.tracer.spans() if s.name.startswith(self.prefix+".")])
    def errors(self):return [s for s in self.tracer.spans() if s.name.startswith(self.prefix+".") and s.status=="error"]
    def durations(self):return [s.duration_ms for s in self.tracer.spans() if s.name.startswith(self.prefix+".") and s.duration_ms is not None]
    def average_duration(self):
        v=self.durations();return sum(v)/len(v) if v else 0


class TraceDomain19:
    """Trace namespace for subsystem 19."""
    def __init__(self,tracer=None):self.tracer=tracer or Tracer();self.prefix="subsystem_19"
    def name(self,key):return f"{self.prefix}.{key}"
    def span(self,key,**kw):return self.tracer.span(self.name(key),**kw)
    def start(self,key,**kw):return self.tracer.start_span(self.name(key),**kw)
    def find(self,key):return self.tracer.find_by_name(self.name(key))
    def names(self):return sorted(set(s.name for s in self.tracer.spans() if s.name.startswith(self.prefix+".")))
    def count(self):return len([s for s in self.tracer.spans() if s.name.startswith(self.prefix+".")])
    def errors(self):return [s for s in self.tracer.spans() if s.name.startswith(self.prefix+".") and s.status=="error"]
    def durations(self):return [s.duration_ms for s in self.tracer.spans() if s.name.startswith(self.prefix+".") and s.duration_ms is not None]
    def average_duration(self):
        v=self.durations();return sum(v)/len(v) if v else 0


class TraceDomain20:
    """Trace namespace for subsystem 20."""
    def __init__(self,tracer=None):self.tracer=tracer or Tracer();self.prefix="subsystem_20"
    def name(self,key):return f"{self.prefix}.{key}"
    def span(self,key,**kw):return self.tracer.span(self.name(key),**kw)
    def start(self,key,**kw):return self.tracer.start_span(self.name(key),**kw)
    def find(self,key):return self.tracer.find_by_name(self.name(key))
    def names(self):return sorted(set(s.name for s in self.tracer.spans() if s.name.startswith(self.prefix+".")))
    def count(self):return len([s for s in self.tracer.spans() if s.name.startswith(self.prefix+".")])
    def errors(self):return [s for s in self.tracer.spans() if s.name.startswith(self.prefix+".") and s.status=="error"]
    def durations(self):return [s.duration_ms for s in self.tracer.spans() if s.name.startswith(self.prefix+".") and s.duration_ms is not None]
    def average_duration(self):
        v=self.durations();return sum(v)/len(v) if v else 0


class TraceDomain21:
    """Trace namespace for subsystem 21."""
    def __init__(self,tracer=None):self.tracer=tracer or Tracer();self.prefix="subsystem_21"
    def name(self,key):return f"{self.prefix}.{key}"
    def span(self,key,**kw):return self.tracer.span(self.name(key),**kw)
    def start(self,key,**kw):return self.tracer.start_span(self.name(key),**kw)
    def find(self,key):return self.tracer.find_by_name(self.name(key))
    def names(self):return sorted(set(s.name for s in self.tracer.spans() if s.name.startswith(self.prefix+".")))
    def count(self):return len([s for s in self.tracer.spans() if s.name.startswith(self.prefix+".")])
    def errors(self):return [s for s in self.tracer.spans() if s.name.startswith(self.prefix+".") and s.status=="error"]
    def durations(self):return [s.duration_ms for s in self.tracer.spans() if s.name.startswith(self.prefix+".") and s.duration_ms is not None]
    def average_duration(self):
        v=self.durations();return sum(v)/len(v) if v else 0


class TraceDomain22:
    """Trace namespace for subsystem 22."""
    def __init__(self,tracer=None):self.tracer=tracer or Tracer();self.prefix="subsystem_22"
    def name(self,key):return f"{self.prefix}.{key}"
    def span(self,key,**kw):return self.tracer.span(self.name(key),**kw)
    def start(self,key,**kw):return self.tracer.start_span(self.name(key),**kw)
    def find(self,key):return self.tracer.find_by_name(self.name(key))
    def names(self):return sorted(set(s.name for s in self.tracer.spans() if s.name.startswith(self.prefix+".")))
    def count(self):return len([s for s in self.tracer.spans() if s.name.startswith(self.prefix+".")])
    def errors(self):return [s for s in self.tracer.spans() if s.name.startswith(self.prefix+".") and s.status=="error"]
    def durations(self):return [s.duration_ms for s in self.tracer.spans() if s.name.startswith(self.prefix+".") and s.duration_ms is not None]
    def average_duration(self):
        v=self.durations();return sum(v)/len(v) if v else 0


class TraceDomain23:
    """Trace namespace for subsystem 23."""
    def __init__(self,tracer=None):self.tracer=tracer or Tracer();self.prefix="subsystem_23"
    def name(self,key):return f"{self.prefix}.{key}"
    def span(self,key,**kw):return self.tracer.span(self.name(key),**kw)
    def start(self,key,**kw):return self.tracer.start_span(self.name(key),**kw)
    def find(self,key):return self.tracer.find_by_name(self.name(key))
    def names(self):return sorted(set(s.name for s in self.tracer.spans() if s.name.startswith(self.prefix+".")))
    def count(self):return len([s for s in self.tracer.spans() if s.name.startswith(self.prefix+".")])
    def errors(self):return [s for s in self.tracer.spans() if s.name.startswith(self.prefix+".") and s.status=="error"]
    def durations(self):return [s.duration_ms for s in self.tracer.spans() if s.name.startswith(self.prefix+".") and s.duration_ms is not None]
    def average_duration(self):
        v=self.durations();return sum(v)/len(v) if v else 0


class TraceDomain24:
    """Trace namespace for subsystem 24."""
    def __init__(self,tracer=None):self.tracer=tracer or Tracer();self.prefix="subsystem_24"
    def name(self,key):return f"{self.prefix}.{key}"
    def span(self,key,**kw):return self.tracer.span(self.name(key),**kw)
    def start(self,key,**kw):return self.tracer.start_span(self.name(key),**kw)
    def find(self,key):return self.tracer.find_by_name(self.name(key))
    def names(self):return sorted(set(s.name for s in self.tracer.spans() if s.name.startswith(self.prefix+".")))
    def count(self):return len([s for s in self.tracer.spans() if s.name.startswith(self.prefix+".")])
    def errors(self):return [s for s in self.tracer.spans() if s.name.startswith(self.prefix+".") and s.status=="error"]
    def durations(self):return [s.duration_ms for s in self.tracer.spans() if s.name.startswith(self.prefix+".") and s.duration_ms is not None]
    def average_duration(self):
        v=self.durations();return sum(v)/len(v) if v else 0


class TraceDomain25:
    """Trace namespace for subsystem 25."""
    def __init__(self,tracer=None):self.tracer=tracer or Tracer();self.prefix="subsystem_25"
    def name(self,key):return f"{self.prefix}.{key}"
    def span(self,key,**kw):return self.tracer.span(self.name(key),**kw)
    def start(self,key,**kw):return self.tracer.start_span(self.name(key),**kw)
    def find(self,key):return self.tracer.find_by_name(self.name(key))
    def names(self):return sorted(set(s.name for s in self.tracer.spans() if s.name.startswith(self.prefix+".")))
    def count(self):return len([s for s in self.tracer.spans() if s.name.startswith(self.prefix+".")])
    def errors(self):return [s for s in self.tracer.spans() if s.name.startswith(self.prefix+".") and s.status=="error"]
    def durations(self):return [s.duration_ms for s in self.tracer.spans() if s.name.startswith(self.prefix+".") and s.duration_ms is not None]
    def average_duration(self):
        v=self.durations();return sum(v)/len(v) if v else 0


class TraceDomain26:
    """Trace namespace for subsystem 26."""
    def __init__(self,tracer=None):self.tracer=tracer or Tracer();self.prefix="subsystem_26"
    def name(self,key):return f"{self.prefix}.{key}"
    def span(self,key,**kw):return self.tracer.span(self.name(key),**kw)
    def start(self,key,**kw):return self.tracer.start_span(self.name(key),**kw)
    def find(self,key):return self.tracer.find_by_name(self.name(key))
    def names(self):return sorted(set(s.name for s in self.tracer.spans() if s.name.startswith(self.prefix+".")))
    def count(self):return len([s for s in self.tracer.spans() if s.name.startswith(self.prefix+".")])
    def errors(self):return [s for s in self.tracer.spans() if s.name.startswith(self.prefix+".") and s.status=="error"]
    def durations(self):return [s.duration_ms for s in self.tracer.spans() if s.name.startswith(self.prefix+".") and s.duration_ms is not None]
    def average_duration(self):
        v=self.durations();return sum(v)/len(v) if v else 0


class TraceDomain27:
    """Trace namespace for subsystem 27."""
    def __init__(self,tracer=None):self.tracer=tracer or Tracer();self.prefix="subsystem_27"
    def name(self,key):return f"{self.prefix}.{key}"
    def span(self,key,**kw):return self.tracer.span(self.name(key),**kw)
    def start(self,key,**kw):return self.tracer.start_span(self.name(key),**kw)
    def find(self,key):return self.tracer.find_by_name(self.name(key))
    def names(self):return sorted(set(s.name for s in self.tracer.spans() if s.name.startswith(self.prefix+".")))
    def count(self):return len([s for s in self.tracer.spans() if s.name.startswith(self.prefix+".")])
    def errors(self):return [s for s in self.tracer.spans() if s.name.startswith(self.prefix+".") and s.status=="error"]
    def durations(self):return [s.duration_ms for s in self.tracer.spans() if s.name.startswith(self.prefix+".") and s.duration_ms is not None]
    def average_duration(self):
        v=self.durations();return sum(v)/len(v) if v else 0


class TraceDomain28:
    """Trace namespace for subsystem 28."""
    def __init__(self,tracer=None):self.tracer=tracer or Tracer();self.prefix="subsystem_28"
    def name(self,key):return f"{self.prefix}.{key}"
    def span(self,key,**kw):return self.tracer.span(self.name(key),**kw)
    def start(self,key,**kw):return self.tracer.start_span(self.name(key),**kw)
    def find(self,key):return self.tracer.find_by_name(self.name(key))
    def names(self):return sorted(set(s.name for s in self.tracer.spans() if s.name.startswith(self.prefix+".")))
    def count(self):return len([s for s in self.tracer.spans() if s.name.startswith(self.prefix+".")])
    def errors(self):return [s for s in self.tracer.spans() if s.name.startswith(self.prefix+".") and s.status=="error"]
    def durations(self):return [s.duration_ms for s in self.tracer.spans() if s.name.startswith(self.prefix+".") and s.duration_ms is not None]
    def average_duration(self):
        v=self.durations();return sum(v)/len(v) if v else 0


class TraceDomain29:
    """Trace namespace for subsystem 29."""
    def __init__(self,tracer=None):self.tracer=tracer or Tracer();self.prefix="subsystem_29"
    def name(self,key):return f"{self.prefix}.{key}"
    def span(self,key,**kw):return self.tracer.span(self.name(key),**kw)
    def start(self,key,**kw):return self.tracer.start_span(self.name(key),**kw)
    def find(self,key):return self.tracer.find_by_name(self.name(key))
    def names(self):return sorted(set(s.name for s in self.tracer.spans() if s.name.startswith(self.prefix+".")))
    def count(self):return len([s for s in self.tracer.spans() if s.name.startswith(self.prefix+".")])
    def errors(self):return [s for s in self.tracer.spans() if s.name.startswith(self.prefix+".") and s.status=="error"]
    def durations(self):return [s.duration_ms for s in self.tracer.spans() if s.name.startswith(self.prefix+".") and s.duration_ms is not None]
    def average_duration(self):
        v=self.durations();return sum(v)/len(v) if v else 0


class TraceDomain30:
    """Trace namespace for subsystem 30."""
    def __init__(self,tracer=None):self.tracer=tracer or Tracer();self.prefix="subsystem_30"
    def name(self,key):return f"{self.prefix}.{key}"
    def span(self,key,**kw):return self.tracer.span(self.name(key),**kw)
    def start(self,key,**kw):return self.tracer.start_span(self.name(key),**kw)
    def find(self,key):return self.tracer.find_by_name(self.name(key))
    def names(self):return sorted(set(s.name for s in self.tracer.spans() if s.name.startswith(self.prefix+".")))
    def count(self):return len([s for s in self.tracer.spans() if s.name.startswith(self.prefix+".")])
    def errors(self):return [s for s in self.tracer.spans() if s.name.startswith(self.prefix+".") and s.status=="error"]
    def durations(self):return [s.duration_ms for s in self.tracer.spans() if s.name.startswith(self.prefix+".") and s.duration_ms is not None]
    def average_duration(self):
        v=self.durations();return sum(v)/len(v) if v else 0


class TraceDomain31:
    """Trace namespace for subsystem 31."""
    def __init__(self,tracer=None):self.tracer=tracer or Tracer();self.prefix="subsystem_31"
    def name(self,key):return f"{self.prefix}.{key}"
    def span(self,key,**kw):return self.tracer.span(self.name(key),**kw)
    def start(self,key,**kw):return self.tracer.start_span(self.name(key),**kw)
    def find(self,key):return self.tracer.find_by_name(self.name(key))
    def names(self):return sorted(set(s.name for s in self.tracer.spans() if s.name.startswith(self.prefix+".")))
    def count(self):return len([s for s in self.tracer.spans() if s.name.startswith(self.prefix+".")])
    def errors(self):return [s for s in self.tracer.spans() if s.name.startswith(self.prefix+".") and s.status=="error"]
    def durations(self):return [s.duration_ms for s in self.tracer.spans() if s.name.startswith(self.prefix+".") and s.duration_ms is not None]
    def average_duration(self):
        v=self.durations();return sum(v)/len(v) if v else 0


class TraceDomain32:
    """Trace namespace for subsystem 32."""
    def __init__(self,tracer=None):self.tracer=tracer or Tracer();self.prefix="subsystem_32"
    def name(self,key):return f"{self.prefix}.{key}"
    def span(self,key,**kw):return self.tracer.span(self.name(key),**kw)
    def start(self,key,**kw):return self.tracer.start_span(self.name(key),**kw)
    def find(self,key):return self.tracer.find_by_name(self.name(key))
    def names(self):return sorted(set(s.name for s in self.tracer.spans() if s.name.startswith(self.prefix+".")))
    def count(self):return len([s for s in self.tracer.spans() if s.name.startswith(self.prefix+".")])
    def errors(self):return [s for s in self.tracer.spans() if s.name.startswith(self.prefix+".") and s.status=="error"]
    def durations(self):return [s.duration_ms for s in self.tracer.spans() if s.name.startswith(self.prefix+".") and s.duration_ms is not None]
    def average_duration(self):
        v=self.durations();return sum(v)/len(v) if v else 0


class TraceDomain33:
    """Trace namespace for subsystem 33."""
    def __init__(self,tracer=None):self.tracer=tracer or Tracer();self.prefix="subsystem_33"
    def name(self,key):return f"{self.prefix}.{key}"
    def span(self,key,**kw):return self.tracer.span(self.name(key),**kw)
    def start(self,key,**kw):return self.tracer.start_span(self.name(key),**kw)
    def find(self,key):return self.tracer.find_by_name(self.name(key))
    def names(self):return sorted(set(s.name for s in self.tracer.spans() if s.name.startswith(self.prefix+".")))
    def count(self):return len([s for s in self.tracer.spans() if s.name.startswith(self.prefix+".")])
    def errors(self):return [s for s in self.tracer.spans() if s.name.startswith(self.prefix+".") and s.status=="error"]
    def durations(self):return [s.duration_ms for s in self.tracer.spans() if s.name.startswith(self.prefix+".") and s.duration_ms is not None]
    def average_duration(self):
        v=self.durations();return sum(v)/len(v) if v else 0


class TraceDomain34:
    """Trace namespace for subsystem 34."""
    def __init__(self,tracer=None):self.tracer=tracer or Tracer();self.prefix="subsystem_34"
    def name(self,key):return f"{self.prefix}.{key}"
    def span(self,key,**kw):return self.tracer.span(self.name(key),**kw)
    def start(self,key,**kw):return self.tracer.start_span(self.name(key),**kw)
    def find(self,key):return self.tracer.find_by_name(self.name(key))
    def names(self):return sorted(set(s.name for s in self.tracer.spans() if s.name.startswith(self.prefix+".")))
    def count(self):return len([s for s in self.tracer.spans() if s.name.startswith(self.prefix+".")])
    def errors(self):return [s for s in self.tracer.spans() if s.name.startswith(self.prefix+".") and s.status=="error"]
    def durations(self):return [s.duration_ms for s in self.tracer.spans() if s.name.startswith(self.prefix+".") and s.duration_ms is not None]
    def average_duration(self):
        v=self.durations();return sum(v)/len(v) if v else 0


class TraceDomain35:
    """Trace namespace for subsystem 35."""
    def __init__(self,tracer=None):self.tracer=tracer or Tracer();self.prefix="subsystem_35"
    def name(self,key):return f"{self.prefix}.{key}"
    def span(self,key,**kw):return self.tracer.span(self.name(key),**kw)
    def start(self,key,**kw):return self.tracer.start_span(self.name(key),**kw)
    def find(self,key):return self.tracer.find_by_name(self.name(key))
    def names(self):return sorted(set(s.name for s in self.tracer.spans() if s.name.startswith(self.prefix+".")))
    def count(self):return len([s for s in self.tracer.spans() if s.name.startswith(self.prefix+".")])
    def errors(self):return [s for s in self.tracer.spans() if s.name.startswith(self.prefix+".") and s.status=="error"]
    def durations(self):return [s.duration_ms for s in self.tracer.spans() if s.name.startswith(self.prefix+".") and s.duration_ms is not None]
    def average_duration(self):
        v=self.durations();return sum(v)/len(v) if v else 0


class TraceDomain36:
    """Trace namespace for subsystem 36."""
    def __init__(self,tracer=None):self.tracer=tracer or Tracer();self.prefix="subsystem_36"
    def name(self,key):return f"{self.prefix}.{key}"
    def span(self,key,**kw):return self.tracer.span(self.name(key),**kw)
    def start(self,key,**kw):return self.tracer.start_span(self.name(key),**kw)
    def find(self,key):return self.tracer.find_by_name(self.name(key))
    def names(self):return sorted(set(s.name for s in self.tracer.spans() if s.name.startswith(self.prefix+".")))
    def count(self):return len([s for s in self.tracer.spans() if s.name.startswith(self.prefix+".")])
    def errors(self):return [s for s in self.tracer.spans() if s.name.startswith(self.prefix+".") and s.status=="error"]
    def durations(self):return [s.duration_ms for s in self.tracer.spans() if s.name.startswith(self.prefix+".") and s.duration_ms is not None]
    def average_duration(self):
        v=self.durations();return sum(v)/len(v) if v else 0


class TraceDomain37:
    """Trace namespace for subsystem 37."""
    def __init__(self,tracer=None):self.tracer=tracer or Tracer();self.prefix="subsystem_37"
    def name(self,key):return f"{self.prefix}.{key}"
    def span(self,key,**kw):return self.tracer.span(self.name(key),**kw)
    def start(self,key,**kw):return self.tracer.start_span(self.name(key),**kw)
    def find(self,key):return self.tracer.find_by_name(self.name(key))
    def names(self):return sorted(set(s.name for s in self.tracer.spans() if s.name.startswith(self.prefix+".")))
    def count(self):return len([s for s in self.tracer.spans() if s.name.startswith(self.prefix+".")])
    def errors(self):return [s for s in self.tracer.spans() if s.name.startswith(self.prefix+".") and s.status=="error"]
    def durations(self):return [s.duration_ms for s in self.tracer.spans() if s.name.startswith(self.prefix+".") and s.duration_ms is not None]
    def average_duration(self):
        v=self.durations();return sum(v)/len(v) if v else 0


class TraceDomain38:
    """Trace namespace for subsystem 38."""
    def __init__(self,tracer=None):self.tracer=tracer or Tracer();self.prefix="subsystem_38"
    def name(self,key):return f"{self.prefix}.{key}"
    def span(self,key,**kw):return self.tracer.span(self.name(key),**kw)
    def start(self,key,**kw):return self.tracer.start_span(self.name(key),**kw)
    def find(self,key):return self.tracer.find_by_name(self.name(key))
    def names(self):return sorted(set(s.name for s in self.tracer.spans() if s.name.startswith(self.prefix+".")))
    def count(self):return len([s for s in self.tracer.spans() if s.name.startswith(self.prefix+".")])
    def errors(self):return [s for s in self.tracer.spans() if s.name.startswith(self.prefix+".") and s.status=="error"]
    def durations(self):return [s.duration_ms for s in self.tracer.spans() if s.name.startswith(self.prefix+".") and s.duration_ms is not None]
    def average_duration(self):
        v=self.durations();return sum(v)/len(v) if v else 0


class TraceDomain39:
    """Trace namespace for subsystem 39."""
    def __init__(self,tracer=None):self.tracer=tracer or Tracer();self.prefix="subsystem_39"
    def name(self,key):return f"{self.prefix}.{key}"
    def span(self,key,**kw):return self.tracer.span(self.name(key),**kw)
    def start(self,key,**kw):return self.tracer.start_span(self.name(key),**kw)
    def find(self,key):return self.tracer.find_by_name(self.name(key))
    def names(self):return sorted(set(s.name for s in self.tracer.spans() if s.name.startswith(self.prefix+".")))
    def count(self):return len([s for s in self.tracer.spans() if s.name.startswith(self.prefix+".")])
    def errors(self):return [s for s in self.tracer.spans() if s.name.startswith(self.prefix+".") and s.status=="error"]
    def durations(self):return [s.duration_ms for s in self.tracer.spans() if s.name.startswith(self.prefix+".") and s.duration_ms is not None]
    def average_duration(self):
        v=self.durations();return sum(v)/len(v) if v else 0


class TraceDomain40:
    """Trace namespace for subsystem 40."""
    def __init__(self,tracer=None):self.tracer=tracer or Tracer();self.prefix="subsystem_40"
    def name(self,key):return f"{self.prefix}.{key}"
    def span(self,key,**kw):return self.tracer.span(self.name(key),**kw)
    def start(self,key,**kw):return self.tracer.start_span(self.name(key),**kw)
    def find(self,key):return self.tracer.find_by_name(self.name(key))
    def names(self):return sorted(set(s.name for s in self.tracer.spans() if s.name.startswith(self.prefix+".")))
    def count(self):return len([s for s in self.tracer.spans() if s.name.startswith(self.prefix+".")])
    def errors(self):return [s for s in self.tracer.spans() if s.name.startswith(self.prefix+".") and s.status=="error"]
    def durations(self):return [s.duration_ms for s in self.tracer.spans() if s.name.startswith(self.prefix+".") and s.duration_ms is not None]
    def average_duration(self):
        v=self.durations();return sum(v)/len(v) if v else 0


class TraceDomain41:
    """Trace namespace for subsystem 41."""
    def __init__(self,tracer=None):self.tracer=tracer or Tracer();self.prefix="subsystem_41"
    def name(self,key):return f"{self.prefix}.{key}"
    def span(self,key,**kw):return self.tracer.span(self.name(key),**kw)
    def start(self,key,**kw):return self.tracer.start_span(self.name(key),**kw)
    def find(self,key):return self.tracer.find_by_name(self.name(key))
    def names(self):return sorted(set(s.name for s in self.tracer.spans() if s.name.startswith(self.prefix+".")))
    def count(self):return len([s for s in self.tracer.spans() if s.name.startswith(self.prefix+".")])
    def errors(self):return [s for s in self.tracer.spans() if s.name.startswith(self.prefix+".") and s.status=="error"]
    def durations(self):return [s.duration_ms for s in self.tracer.spans() if s.name.startswith(self.prefix+".") and s.duration_ms is not None]
    def average_duration(self):
        v=self.durations();return sum(v)/len(v) if v else 0


class TraceDomain42:
    """Trace namespace for subsystem 42."""
    def __init__(self,tracer=None):self.tracer=tracer or Tracer();self.prefix="subsystem_42"
    def name(self,key):return f"{self.prefix}.{key}"
    def span(self,key,**kw):return self.tracer.span(self.name(key),**kw)
    def start(self,key,**kw):return self.tracer.start_span(self.name(key),**kw)
    def find(self,key):return self.tracer.find_by_name(self.name(key))
    def names(self):return sorted(set(s.name for s in self.tracer.spans() if s.name.startswith(self.prefix+".")))
    def count(self):return len([s for s in self.tracer.spans() if s.name.startswith(self.prefix+".")])
    def errors(self):return [s for s in self.tracer.spans() if s.name.startswith(self.prefix+".") and s.status=="error"]
    def durations(self):return [s.duration_ms for s in self.tracer.spans() if s.name.startswith(self.prefix+".") and s.duration_ms is not None]
    def average_duration(self):
        v=self.durations();return sum(v)/len(v) if v else 0


class TraceDomain43:
    """Trace namespace for subsystem 43."""
    def __init__(self,tracer=None):self.tracer=tracer or Tracer();self.prefix="subsystem_43"
    def name(self,key):return f"{self.prefix}.{key}"
    def span(self,key,**kw):return self.tracer.span(self.name(key),**kw)
    def start(self,key,**kw):return self.tracer.start_span(self.name(key),**kw)
    def find(self,key):return self.tracer.find_by_name(self.name(key))
    def names(self):return sorted(set(s.name for s in self.tracer.spans() if s.name.startswith(self.prefix+".")))
    def count(self):return len([s for s in self.tracer.spans() if s.name.startswith(self.prefix+".")])
    def errors(self):return [s for s in self.tracer.spans() if s.name.startswith(self.prefix+".") and s.status=="error"]
    def durations(self):return [s.duration_ms for s in self.tracer.spans() if s.name.startswith(self.prefix+".") and s.duration_ms is not None]
    def average_duration(self):
        v=self.durations();return sum(v)/len(v) if v else 0


class TraceDomain44:
    """Trace namespace for subsystem 44."""
    def __init__(self,tracer=None):self.tracer=tracer or Tracer();self.prefix="subsystem_44"
    def name(self,key):return f"{self.prefix}.{key}"
    def span(self,key,**kw):return self.tracer.span(self.name(key),**kw)
    def start(self,key,**kw):return self.tracer.start_span(self.name(key),**kw)
    def find(self,key):return self.tracer.find_by_name(self.name(key))
    def names(self):return sorted(set(s.name for s in self.tracer.spans() if s.name.startswith(self.prefix+".")))
    def count(self):return len([s for s in self.tracer.spans() if s.name.startswith(self.prefix+".")])
    def errors(self):return [s for s in self.tracer.spans() if s.name.startswith(self.prefix+".") and s.status=="error"]
    def durations(self):return [s.duration_ms for s in self.tracer.spans() if s.name.startswith(self.prefix+".") and s.duration_ms is not None]
    def average_duration(self):
        v=self.durations();return sum(v)/len(v) if v else 0


class TraceDomain45:
    """Trace namespace for subsystem 45."""
    def __init__(self,tracer=None):self.tracer=tracer or Tracer();self.prefix="subsystem_45"
    def name(self,key):return f"{self.prefix}.{key}"
    def span(self,key,**kw):return self.tracer.span(self.name(key),**kw)
    def start(self,key,**kw):return self.tracer.start_span(self.name(key),**kw)
    def find(self,key):return self.tracer.find_by_name(self.name(key))
    def names(self):return sorted(set(s.name for s in self.tracer.spans() if s.name.startswith(self.prefix+".")))
    def count(self):return len([s for s in self.tracer.spans() if s.name.startswith(self.prefix+".")])
    def errors(self):return [s for s in self.tracer.spans() if s.name.startswith(self.prefix+".") and s.status=="error"]
    def durations(self):return [s.duration_ms for s in self.tracer.spans() if s.name.startswith(self.prefix+".") and s.duration_ms is not None]
    def average_duration(self):
        v=self.durations();return sum(v)/len(v) if v else 0


class TraceDomain46:
    """Trace namespace for subsystem 46."""
    def __init__(self,tracer=None):self.tracer=tracer or Tracer();self.prefix="subsystem_46"
    def name(self,key):return f"{self.prefix}.{key}"
    def span(self,key,**kw):return self.tracer.span(self.name(key),**kw)
    def start(self,key,**kw):return self.tracer.start_span(self.name(key),**kw)
    def find(self,key):return self.tracer.find_by_name(self.name(key))
    def names(self):return sorted(set(s.name for s in self.tracer.spans() if s.name.startswith(self.prefix+".")))
    def count(self):return len([s for s in self.tracer.spans() if s.name.startswith(self.prefix+".")])
    def errors(self):return [s for s in self.tracer.spans() if s.name.startswith(self.prefix+".") and s.status=="error"]
    def durations(self):return [s.duration_ms for s in self.tracer.spans() if s.name.startswith(self.prefix+".") and s.duration_ms is not None]
    def average_duration(self):
        v=self.durations();return sum(v)/len(v) if v else 0


class TraceDomain47:
    """Trace namespace for subsystem 47."""
    def __init__(self,tracer=None):self.tracer=tracer or Tracer();self.prefix="subsystem_47"
    def name(self,key):return f"{self.prefix}.{key}"
    def span(self,key,**kw):return self.tracer.span(self.name(key),**kw)
    def start(self,key,**kw):return self.tracer.start_span(self.name(key),**kw)
    def find(self,key):return self.tracer.find_by_name(self.name(key))
    def names(self):return sorted(set(s.name for s in self.tracer.spans() if s.name.startswith(self.prefix+".")))
    def count(self):return len([s for s in self.tracer.spans() if s.name.startswith(self.prefix+".")])
    def errors(self):return [s for s in self.tracer.spans() if s.name.startswith(self.prefix+".") and s.status=="error"]
    def durations(self):return [s.duration_ms for s in self.tracer.spans() if s.name.startswith(self.prefix+".") and s.duration_ms is not None]
    def average_duration(self):
        v=self.durations();return sum(v)/len(v) if v else 0


class TraceDomain48:
    """Trace namespace for subsystem 48."""
    def __init__(self,tracer=None):self.tracer=tracer or Tracer();self.prefix="subsystem_48"
    def name(self,key):return f"{self.prefix}.{key}"
    def span(self,key,**kw):return self.tracer.span(self.name(key),**kw)
    def start(self,key,**kw):return self.tracer.start_span(self.name(key),**kw)
    def find(self,key):return self.tracer.find_by_name(self.name(key))
    def names(self):return sorted(set(s.name for s in self.tracer.spans() if s.name.startswith(self.prefix+".")))
    def count(self):return len([s for s in self.tracer.spans() if s.name.startswith(self.prefix+".")])
    def errors(self):return [s for s in self.tracer.spans() if s.name.startswith(self.prefix+".") and s.status=="error"]
    def durations(self):return [s.duration_ms for s in self.tracer.spans() if s.name.startswith(self.prefix+".") and s.duration_ms is not None]
    def average_duration(self):
        v=self.durations();return sum(v)/len(v) if v else 0


class TraceDomain49:
    """Trace namespace for subsystem 49."""
    def __init__(self,tracer=None):self.tracer=tracer or Tracer();self.prefix="subsystem_49"
    def name(self,key):return f"{self.prefix}.{key}"
    def span(self,key,**kw):return self.tracer.span(self.name(key),**kw)
    def start(self,key,**kw):return self.tracer.start_span(self.name(key),**kw)
    def find(self,key):return self.tracer.find_by_name(self.name(key))
    def names(self):return sorted(set(s.name for s in self.tracer.spans() if s.name.startswith(self.prefix+".")))
    def count(self):return len([s for s in self.tracer.spans() if s.name.startswith(self.prefix+".")])
    def errors(self):return [s for s in self.tracer.spans() if s.name.startswith(self.prefix+".") and s.status=="error"]
    def durations(self):return [s.duration_ms for s in self.tracer.spans() if s.name.startswith(self.prefix+".") and s.duration_ms is not None]
    def average_duration(self):
        v=self.durations();return sum(v)/len(v) if v else 0


class TraceDomain50:
    """Trace namespace for subsystem 50."""
    def __init__(self,tracer=None):self.tracer=tracer or Tracer();self.prefix="subsystem_50"
    def name(self,key):return f"{self.prefix}.{key}"
    def span(self,key,**kw):return self.tracer.span(self.name(key),**kw)
    def start(self,key,**kw):return self.tracer.start_span(self.name(key),**kw)
    def find(self,key):return self.tracer.find_by_name(self.name(key))
    def names(self):return sorted(set(s.name for s in self.tracer.spans() if s.name.startswith(self.prefix+".")))
    def count(self):return len([s for s in self.tracer.spans() if s.name.startswith(self.prefix+".")])
    def errors(self):return [s for s in self.tracer.spans() if s.name.startswith(self.prefix+".") and s.status=="error"]
    def durations(self):return [s.duration_ms for s in self.tracer.spans() if s.name.startswith(self.prefix+".") and s.duration_ms is not None]
    def average_duration(self):
        v=self.durations();return sum(v)/len(v) if v else 0


class TraceDomain51:
    """Trace namespace for subsystem 51."""
    def __init__(self,tracer=None):self.tracer=tracer or Tracer();self.prefix="subsystem_51"
    def name(self,key):return f"{self.prefix}.{key}"
    def span(self,key,**kw):return self.tracer.span(self.name(key),**kw)
    def start(self,key,**kw):return self.tracer.start_span(self.name(key),**kw)
    def find(self,key):return self.tracer.find_by_name(self.name(key))
    def names(self):return sorted(set(s.name for s in self.tracer.spans() if s.name.startswith(self.prefix+".")))
    def count(self):return len([s for s in self.tracer.spans() if s.name.startswith(self.prefix+".")])
    def errors(self):return [s for s in self.tracer.spans() if s.name.startswith(self.prefix+".") and s.status=="error"]
    def durations(self):return [s.duration_ms for s in self.tracer.spans() if s.name.startswith(self.prefix+".") and s.duration_ms is not None]
    def average_duration(self):
        v=self.durations();return sum(v)/len(v) if v else 0


class TraceDomain52:
    """Trace namespace for subsystem 52."""
    def __init__(self,tracer=None):self.tracer=tracer or Tracer();self.prefix="subsystem_52"
    def name(self,key):return f"{self.prefix}.{key}"
    def span(self,key,**kw):return self.tracer.span(self.name(key),**kw)
    def start(self,key,**kw):return self.tracer.start_span(self.name(key),**kw)
    def find(self,key):return self.tracer.find_by_name(self.name(key))
    def names(self):return sorted(set(s.name for s in self.tracer.spans() if s.name.startswith(self.prefix+".")))
    def count(self):return len([s for s in self.tracer.spans() if s.name.startswith(self.prefix+".")])
    def errors(self):return [s for s in self.tracer.spans() if s.name.startswith(self.prefix+".") and s.status=="error"]
    def durations(self):return [s.duration_ms for s in self.tracer.spans() if s.name.startswith(self.prefix+".") and s.duration_ms is not None]
    def average_duration(self):
        v=self.durations();return sum(v)/len(v) if v else 0


class TraceDomain53:
    """Trace namespace for subsystem 53."""
    def __init__(self,tracer=None):self.tracer=tracer or Tracer();self.prefix="subsystem_53"
    def name(self,key):return f"{self.prefix}.{key}"
    def span(self,key,**kw):return self.tracer.span(self.name(key),**kw)
    def start(self,key,**kw):return self.tracer.start_span(self.name(key),**kw)
    def find(self,key):return self.tracer.find_by_name(self.name(key))
    def names(self):return sorted(set(s.name for s in self.tracer.spans() if s.name.startswith(self.prefix+".")))
    def count(self):return len([s for s in self.tracer.spans() if s.name.startswith(self.prefix+".")])
    def errors(self):return [s for s in self.tracer.spans() if s.name.startswith(self.prefix+".") and s.status=="error"]
    def durations(self):return [s.duration_ms for s in self.tracer.spans() if s.name.startswith(self.prefix+".") and s.duration_ms is not None]
    def average_duration(self):
        v=self.durations();return sum(v)/len(v) if v else 0


class TraceDomain54:
    """Trace namespace for subsystem 54."""
    def __init__(self,tracer=None):self.tracer=tracer or Tracer();self.prefix="subsystem_54"
    def name(self,key):return f"{self.prefix}.{key}"
    def span(self,key,**kw):return self.tracer.span(self.name(key),**kw)
    def start(self,key,**kw):return self.tracer.start_span(self.name(key),**kw)
    def find(self,key):return self.tracer.find_by_name(self.name(key))
    def names(self):return sorted(set(s.name for s in self.tracer.spans() if s.name.startswith(self.prefix+".")))
    def count(self):return len([s for s in self.tracer.spans() if s.name.startswith(self.prefix+".")])
    def errors(self):return [s for s in self.tracer.spans() if s.name.startswith(self.prefix+".") and s.status=="error"]
    def durations(self):return [s.duration_ms for s in self.tracer.spans() if s.name.startswith(self.prefix+".") and s.duration_ms is not None]
    def average_duration(self):
        v=self.durations();return sum(v)/len(v) if v else 0


class TraceDomain55:
    """Trace namespace for subsystem 55."""
    def __init__(self,tracer=None):self.tracer=tracer or Tracer();self.prefix="subsystem_55"
    def name(self,key):return f"{self.prefix}.{key}"
    def span(self,key,**kw):return self.tracer.span(self.name(key),**kw)
    def start(self,key,**kw):return self.tracer.start_span(self.name(key),**kw)
    def find(self,key):return self.tracer.find_by_name(self.name(key))
    def names(self):return sorted(set(s.name for s in self.tracer.spans() if s.name.startswith(self.prefix+".")))
    def count(self):return len([s for s in self.tracer.spans() if s.name.startswith(self.prefix+".")])
    def errors(self):return [s for s in self.tracer.spans() if s.name.startswith(self.prefix+".") and s.status=="error"]
    def durations(self):return [s.duration_ms for s in self.tracer.spans() if s.name.startswith(self.prefix+".") and s.duration_ms is not None]
    def average_duration(self):
        v=self.durations();return sum(v)/len(v) if v else 0


class TraceDomain56:
    """Trace namespace for subsystem 56."""
    def __init__(self,tracer=None):self.tracer=tracer or Tracer();self.prefix="subsystem_56"
    def name(self,key):return f"{self.prefix}.{key}"
    def span(self,key,**kw):return self.tracer.span(self.name(key),**kw)
    def start(self,key,**kw):return self.tracer.start_span(self.name(key),**kw)
    def find(self,key):return self.tracer.find_by_name(self.name(key))
    def names(self):return sorted(set(s.name for s in self.tracer.spans() if s.name.startswith(self.prefix+".")))
    def count(self):return len([s for s in self.tracer.spans() if s.name.startswith(self.prefix+".")])
    def errors(self):return [s for s in self.tracer.spans() if s.name.startswith(self.prefix+".") and s.status=="error"]
    def durations(self):return [s.duration_ms for s in self.tracer.spans() if s.name.startswith(self.prefix+".") and s.duration_ms is not None]
    def average_duration(self):
        v=self.durations();return sum(v)/len(v) if v else 0


class TraceDomain57:
    """Trace namespace for subsystem 57."""
    def __init__(self,tracer=None):self.tracer=tracer or Tracer();self.prefix="subsystem_57"
    def name(self,key):return f"{self.prefix}.{key}"
    def span(self,key,**kw):return self.tracer.span(self.name(key),**kw)
    def start(self,key,**kw):return self.tracer.start_span(self.name(key),**kw)
    def find(self,key):return self.tracer.find_by_name(self.name(key))
    def names(self):return sorted(set(s.name for s in self.tracer.spans() if s.name.startswith(self.prefix+".")))
    def count(self):return len([s for s in self.tracer.spans() if s.name.startswith(self.prefix+".")])
    def errors(self):return [s for s in self.tracer.spans() if s.name.startswith(self.prefix+".") and s.status=="error"]
    def durations(self):return [s.duration_ms for s in self.tracer.spans() if s.name.startswith(self.prefix+".") and s.duration_ms is not None]
    def average_duration(self):
        v=self.durations();return sum(v)/len(v) if v else 0


class TraceDomain58:
    """Trace namespace for subsystem 58."""
    def __init__(self,tracer=None):self.tracer=tracer or Tracer();self.prefix="subsystem_58"
    def name(self,key):return f"{self.prefix}.{key}"
    def span(self,key,**kw):return self.tracer.span(self.name(key),**kw)
    def start(self,key,**kw):return self.tracer.start_span(self.name(key),**kw)
    def find(self,key):return self.tracer.find_by_name(self.name(key))
    def names(self):return sorted(set(s.name for s in self.tracer.spans() if s.name.startswith(self.prefix+".")))
    def count(self):return len([s for s in self.tracer.spans() if s.name.startswith(self.prefix+".")])
    def errors(self):return [s for s in self.tracer.spans() if s.name.startswith(self.prefix+".") and s.status=="error"]
    def durations(self):return [s.duration_ms for s in self.tracer.spans() if s.name.startswith(self.prefix+".") and s.duration_ms is not None]
    def average_duration(self):
        v=self.durations();return sum(v)/len(v) if v else 0


class TraceDomain59:
    """Trace namespace for subsystem 59."""
    def __init__(self,tracer=None):self.tracer=tracer or Tracer();self.prefix="subsystem_59"
    def name(self,key):return f"{self.prefix}.{key}"
    def span(self,key,**kw):return self.tracer.span(self.name(key),**kw)
    def start(self,key,**kw):return self.tracer.start_span(self.name(key),**kw)
    def find(self,key):return self.tracer.find_by_name(self.name(key))
    def names(self):return sorted(set(s.name for s in self.tracer.spans() if s.name.startswith(self.prefix+".")))
    def count(self):return len([s for s in self.tracer.spans() if s.name.startswith(self.prefix+".")])
    def errors(self):return [s for s in self.tracer.spans() if s.name.startswith(self.prefix+".") and s.status=="error"]
    def durations(self):return [s.duration_ms for s in self.tracer.spans() if s.name.startswith(self.prefix+".") and s.duration_ms is not None]
    def average_duration(self):
        v=self.durations();return sum(v)/len(v) if v else 0


class TraceDomain60:
    """Trace namespace for subsystem 60."""
    def __init__(self,tracer=None):self.tracer=tracer or Tracer();self.prefix="subsystem_60"
    def name(self,key):return f"{self.prefix}.{key}"
    def span(self,key,**kw):return self.tracer.span(self.name(key),**kw)
    def start(self,key,**kw):return self.tracer.start_span(self.name(key),**kw)
    def find(self,key):return self.tracer.find_by_name(self.name(key))
    def names(self):return sorted(set(s.name for s in self.tracer.spans() if s.name.startswith(self.prefix+".")))
    def count(self):return len([s for s in self.tracer.spans() if s.name.startswith(self.prefix+".")])
    def errors(self):return [s for s in self.tracer.spans() if s.name.startswith(self.prefix+".") and s.status=="error"]
    def durations(self):return [s.duration_ms for s in self.tracer.spans() if s.name.startswith(self.prefix+".") and s.duration_ms is not None]
    def average_duration(self):
        v=self.durations();return sum(v)/len(v) if v else 0


class TraceDomain61:
    """Trace namespace for subsystem 61."""
    def __init__(self,tracer=None):self.tracer=tracer or Tracer();self.prefix="subsystem_61"
    def name(self,key):return f"{self.prefix}.{key}"
    def span(self,key,**kw):return self.tracer.span(self.name(key),**kw)
    def start(self,key,**kw):return self.tracer.start_span(self.name(key),**kw)
    def find(self,key):return self.tracer.find_by_name(self.name(key))
    def names(self):return sorted(set(s.name for s in self.tracer.spans() if s.name.startswith(self.prefix+".")))
    def count(self):return len([s for s in self.tracer.spans() if s.name.startswith(self.prefix+".")])
    def errors(self):return [s for s in self.tracer.spans() if s.name.startswith(self.prefix+".") and s.status=="error"]
    def durations(self):return [s.duration_ms for s in self.tracer.spans() if s.name.startswith(self.prefix+".") and s.duration_ms is not None]
    def average_duration(self):
        v=self.durations();return sum(v)/len(v) if v else 0


class TraceDomain62:
    """Trace namespace for subsystem 62."""
    def __init__(self,tracer=None):self.tracer=tracer or Tracer();self.prefix="subsystem_62"
    def name(self,key):return f"{self.prefix}.{key}"
    def span(self,key,**kw):return self.tracer.span(self.name(key),**kw)
    def start(self,key,**kw):return self.tracer.start_span(self.name(key),**kw)
    def find(self,key):return self.tracer.find_by_name(self.name(key))
    def names(self):return sorted(set(s.name for s in self.tracer.spans() if s.name.startswith(self.prefix+".")))
    def count(self):return len([s for s in self.tracer.spans() if s.name.startswith(self.prefix+".")])
    def errors(self):return [s for s in self.tracer.spans() if s.name.startswith(self.prefix+".") and s.status=="error"]
    def durations(self):return [s.duration_ms for s in self.tracer.spans() if s.name.startswith(self.prefix+".") and s.duration_ms is not None]
    def average_duration(self):
        v=self.durations();return sum(v)/len(v) if v else 0


class TraceDomain63:
    """Trace namespace for subsystem 63."""
    def __init__(self,tracer=None):self.tracer=tracer or Tracer();self.prefix="subsystem_63"
    def name(self,key):return f"{self.prefix}.{key}"
    def span(self,key,**kw):return self.tracer.span(self.name(key),**kw)
    def start(self,key,**kw):return self.tracer.start_span(self.name(key),**kw)
    def find(self,key):return self.tracer.find_by_name(self.name(key))
    def names(self):return sorted(set(s.name for s in self.tracer.spans() if s.name.startswith(self.prefix+".")))
    def count(self):return len([s for s in self.tracer.spans() if s.name.startswith(self.prefix+".")])
    def errors(self):return [s for s in self.tracer.spans() if s.name.startswith(self.prefix+".") and s.status=="error"]
    def durations(self):return [s.duration_ms for s in self.tracer.spans() if s.name.startswith(self.prefix+".") and s.duration_ms is not None]
    def average_duration(self):
        v=self.durations();return sum(v)/len(v) if v else 0


class TraceDomain64:
    """Trace namespace for subsystem 64."""
    def __init__(self,tracer=None):self.tracer=tracer or Tracer();self.prefix="subsystem_64"
    def name(self,key):return f"{self.prefix}.{key}"
    def span(self,key,**kw):return self.tracer.span(self.name(key),**kw)
    def start(self,key,**kw):return self.tracer.start_span(self.name(key),**kw)
    def find(self,key):return self.tracer.find_by_name(self.name(key))
    def names(self):return sorted(set(s.name for s in self.tracer.spans() if s.name.startswith(self.prefix+".")))
    def count(self):return len([s for s in self.tracer.spans() if s.name.startswith(self.prefix+".")])
    def errors(self):return [s for s in self.tracer.spans() if s.name.startswith(self.prefix+".") and s.status=="error"]
    def durations(self):return [s.duration_ms for s in self.tracer.spans() if s.name.startswith(self.prefix+".") and s.duration_ms is not None]
    def average_duration(self):
        v=self.durations();return sum(v)/len(v) if v else 0


class TraceDomain65:
    """Trace namespace for subsystem 65."""
    def __init__(self,tracer=None):self.tracer=tracer or Tracer();self.prefix="subsystem_65"
    def name(self,key):return f"{self.prefix}.{key}"
    def span(self,key,**kw):return self.tracer.span(self.name(key),**kw)
    def start(self,key,**kw):return self.tracer.start_span(self.name(key),**kw)
    def find(self,key):return self.tracer.find_by_name(self.name(key))
    def names(self):return sorted(set(s.name for s in self.tracer.spans() if s.name.startswith(self.prefix+".")))
    def count(self):return len([s for s in self.tracer.spans() if s.name.startswith(self.prefix+".")])
    def errors(self):return [s for s in self.tracer.spans() if s.name.startswith(self.prefix+".") and s.status=="error"]
    def durations(self):return [s.duration_ms for s in self.tracer.spans() if s.name.startswith(self.prefix+".") and s.duration_ms is not None]
    def average_duration(self):
        v=self.durations();return sum(v)/len(v) if v else 0


class TraceDomain66:
    """Trace namespace for subsystem 66."""
    def __init__(self,tracer=None):self.tracer=tracer or Tracer();self.prefix="subsystem_66"
    def name(self,key):return f"{self.prefix}.{key}"
    def span(self,key,**kw):return self.tracer.span(self.name(key),**kw)
    def start(self,key,**kw):return self.tracer.start_span(self.name(key),**kw)
    def find(self,key):return self.tracer.find_by_name(self.name(key))
    def names(self):return sorted(set(s.name for s in self.tracer.spans() if s.name.startswith(self.prefix+".")))
    def count(self):return len([s for s in self.tracer.spans() if s.name.startswith(self.prefix+".")])
    def errors(self):return [s for s in self.tracer.spans() if s.name.startswith(self.prefix+".") and s.status=="error"]
    def durations(self):return [s.duration_ms for s in self.tracer.spans() if s.name.startswith(self.prefix+".") and s.duration_ms is not None]
    def average_duration(self):
        v=self.durations();return sum(v)/len(v) if v else 0


class TraceDomain67:
    """Trace namespace for subsystem 67."""
    def __init__(self,tracer=None):self.tracer=tracer or Tracer();self.prefix="subsystem_67"
    def name(self,key):return f"{self.prefix}.{key}"
    def span(self,key,**kw):return self.tracer.span(self.name(key),**kw)
    def start(self,key,**kw):return self.tracer.start_span(self.name(key),**kw)
    def find(self,key):return self.tracer.find_by_name(self.name(key))
    def names(self):return sorted(set(s.name for s in self.tracer.spans() if s.name.startswith(self.prefix+".")))
    def count(self):return len([s for s in self.tracer.spans() if s.name.startswith(self.prefix+".")])
    def errors(self):return [s for s in self.tracer.spans() if s.name.startswith(self.prefix+".") and s.status=="error"]
    def durations(self):return [s.duration_ms for s in self.tracer.spans() if s.name.startswith(self.prefix+".") and s.duration_ms is not None]
    def average_duration(self):
        v=self.durations();return sum(v)/len(v) if v else 0


class TraceDomain68:
    """Trace namespace for subsystem 68."""
    def __init__(self,tracer=None):self.tracer=tracer or Tracer();self.prefix="subsystem_68"
    def name(self,key):return f"{self.prefix}.{key}"
    def span(self,key,**kw):return self.tracer.span(self.name(key),**kw)
    def start(self,key,**kw):return self.tracer.start_span(self.name(key),**kw)
    def find(self,key):return self.tracer.find_by_name(self.name(key))
    def names(self):return sorted(set(s.name for s in self.tracer.spans() if s.name.startswith(self.prefix+".")))
    def count(self):return len([s for s in self.tracer.spans() if s.name.startswith(self.prefix+".")])
    def errors(self):return [s for s in self.tracer.spans() if s.name.startswith(self.prefix+".") and s.status=="error"]
    def durations(self):return [s.duration_ms for s in self.tracer.spans() if s.name.startswith(self.prefix+".") and s.duration_ms is not None]
    def average_duration(self):
        v=self.durations();return sum(v)/len(v) if v else 0


class TraceDomain69:
    """Trace namespace for subsystem 69."""
    def __init__(self,tracer=None):self.tracer=tracer or Tracer();self.prefix="subsystem_69"
    def name(self,key):return f"{self.prefix}.{key}"
    def span(self,key,**kw):return self.tracer.span(self.name(key),**kw)
    def start(self,key,**kw):return self.tracer.start_span(self.name(key),**kw)
    def find(self,key):return self.tracer.find_by_name(self.name(key))
    def names(self):return sorted(set(s.name for s in self.tracer.spans() if s.name.startswith(self.prefix+".")))
    def count(self):return len([s for s in self.tracer.spans() if s.name.startswith(self.prefix+".")])
    def errors(self):return [s for s in self.tracer.spans() if s.name.startswith(self.prefix+".") and s.status=="error"]
    def durations(self):return [s.duration_ms for s in self.tracer.spans() if s.name.startswith(self.prefix+".") and s.duration_ms is not None]
    def average_duration(self):
        v=self.durations();return sum(v)/len(v) if v else 0


class TraceDomain70:
    """Trace namespace for subsystem 70."""
    def __init__(self,tracer=None):self.tracer=tracer or Tracer();self.prefix="subsystem_70"
    def name(self,key):return f"{self.prefix}.{key}"
    def span(self,key,**kw):return self.tracer.span(self.name(key),**kw)
    def start(self,key,**kw):return self.tracer.start_span(self.name(key),**kw)
    def find(self,key):return self.tracer.find_by_name(self.name(key))
    def names(self):return sorted(set(s.name for s in self.tracer.spans() if s.name.startswith(self.prefix+".")))
    def count(self):return len([s for s in self.tracer.spans() if s.name.startswith(self.prefix+".")])
    def errors(self):return [s for s in self.tracer.spans() if s.name.startswith(self.prefix+".") and s.status=="error"]
    def durations(self):return [s.duration_ms for s in self.tracer.spans() if s.name.startswith(self.prefix+".") and s.duration_ms is not None]
    def average_duration(self):
        v=self.durations();return sum(v)/len(v) if v else 0


class TraceDomain71:
    """Trace namespace for subsystem 71."""
    def __init__(self,tracer=None):self.tracer=tracer or Tracer();self.prefix="subsystem_71"
    def name(self,key):return f"{self.prefix}.{key}"
    def span(self,key,**kw):return self.tracer.span(self.name(key),**kw)
    def start(self,key,**kw):return self.tracer.start_span(self.name(key),**kw)
    def find(self,key):return self.tracer.find_by_name(self.name(key))
    def names(self):return sorted(set(s.name for s in self.tracer.spans() if s.name.startswith(self.prefix+".")))
    def count(self):return len([s for s in self.tracer.spans() if s.name.startswith(self.prefix+".")])
    def errors(self):return [s for s in self.tracer.spans() if s.name.startswith(self.prefix+".") and s.status=="error"]
    def durations(self):return [s.duration_ms for s in self.tracer.spans() if s.name.startswith(self.prefix+".") and s.duration_ms is not None]
    def average_duration(self):
        v=self.durations();return sum(v)/len(v) if v else 0


class TraceDomain72:
    """Trace namespace for subsystem 72."""
    def __init__(self,tracer=None):self.tracer=tracer or Tracer();self.prefix="subsystem_72"
    def name(self,key):return f"{self.prefix}.{key}"
    def span(self,key,**kw):return self.tracer.span(self.name(key),**kw)
    def start(self,key,**kw):return self.tracer.start_span(self.name(key),**kw)
    def find(self,key):return self.tracer.find_by_name(self.name(key))
    def names(self):return sorted(set(s.name for s in self.tracer.spans() if s.name.startswith(self.prefix+".")))
    def count(self):return len([s for s in self.tracer.spans() if s.name.startswith(self.prefix+".")])
    def errors(self):return [s for s in self.tracer.spans() if s.name.startswith(self.prefix+".") and s.status=="error"]
    def durations(self):return [s.duration_ms for s in self.tracer.spans() if s.name.startswith(self.prefix+".") and s.duration_ms is not None]
    def average_duration(self):
        v=self.durations();return sum(v)/len(v) if v else 0


class TraceDomain73:
    """Trace namespace for subsystem 73."""
    def __init__(self,tracer=None):self.tracer=tracer or Tracer();self.prefix="subsystem_73"
    def name(self,key):return f"{self.prefix}.{key}"
    def span(self,key,**kw):return self.tracer.span(self.name(key),**kw)
    def start(self,key,**kw):return self.tracer.start_span(self.name(key),**kw)
    def find(self,key):return self.tracer.find_by_name(self.name(key))
    def names(self):return sorted(set(s.name for s in self.tracer.spans() if s.name.startswith(self.prefix+".")))
    def count(self):return len([s for s in self.tracer.spans() if s.name.startswith(self.prefix+".")])
    def errors(self):return [s for s in self.tracer.spans() if s.name.startswith(self.prefix+".") and s.status=="error"]
    def durations(self):return [s.duration_ms for s in self.tracer.spans() if s.name.startswith(self.prefix+".") and s.duration_ms is not None]
    def average_duration(self):
        v=self.durations();return sum(v)/len(v) if v else 0


class TraceDomain74:
    """Trace namespace for subsystem 74."""
    def __init__(self,tracer=None):self.tracer=tracer or Tracer();self.prefix="subsystem_74"
    def name(self,key):return f"{self.prefix}.{key}"
    def span(self,key,**kw):return self.tracer.span(self.name(key),**kw)
    def start(self,key,**kw):return self.tracer.start_span(self.name(key),**kw)
    def find(self,key):return self.tracer.find_by_name(self.name(key))
    def names(self):return sorted(set(s.name for s in self.tracer.spans() if s.name.startswith(self.prefix+".")))
    def count(self):return len([s for s in self.tracer.spans() if s.name.startswith(self.prefix+".")])
    def errors(self):return [s for s in self.tracer.spans() if s.name.startswith(self.prefix+".") and s.status=="error"]
    def durations(self):return [s.duration_ms for s in self.tracer.spans() if s.name.startswith(self.prefix+".") and s.duration_ms is not None]
    def average_duration(self):
        v=self.durations();return sum(v)/len(v) if v else 0


class TraceDomain75:
    """Trace namespace for subsystem 75."""
    def __init__(self,tracer=None):self.tracer=tracer or Tracer();self.prefix="subsystem_75"
    def name(self,key):return f"{self.prefix}.{key}"
    def span(self,key,**kw):return self.tracer.span(self.name(key),**kw)
    def start(self,key,**kw):return self.tracer.start_span(self.name(key),**kw)
    def find(self,key):return self.tracer.find_by_name(self.name(key))
    def names(self):return sorted(set(s.name for s in self.tracer.spans() if s.name.startswith(self.prefix+".")))
    def count(self):return len([s for s in self.tracer.spans() if s.name.startswith(self.prefix+".")])
    def errors(self):return [s for s in self.tracer.spans() if s.name.startswith(self.prefix+".") and s.status=="error"]
    def durations(self):return [s.duration_ms for s in self.tracer.spans() if s.name.startswith(self.prefix+".") and s.duration_ms is not None]
    def average_duration(self):
        v=self.durations();return sum(v)/len(v) if v else 0


class TraceDomain76:
    """Trace namespace for subsystem 76."""
    def __init__(self,tracer=None):self.tracer=tracer or Tracer();self.prefix="subsystem_76"
    def name(self,key):return f"{self.prefix}.{key}"
    def span(self,key,**kw):return self.tracer.span(self.name(key),**kw)
    def start(self,key,**kw):return self.tracer.start_span(self.name(key),**kw)
    def find(self,key):return self.tracer.find_by_name(self.name(key))
    def names(self):return sorted(set(s.name for s in self.tracer.spans() if s.name.startswith(self.prefix+".")))
    def count(self):return len([s for s in self.tracer.spans() if s.name.startswith(self.prefix+".")])
    def errors(self):return [s for s in self.tracer.spans() if s.name.startswith(self.prefix+".") and s.status=="error"]
    def durations(self):return [s.duration_ms for s in self.tracer.spans() if s.name.startswith(self.prefix+".") and s.duration_ms is not None]
    def average_duration(self):
        v=self.durations();return sum(v)/len(v) if v else 0


class TraceDomain77:
    """Trace namespace for subsystem 77."""
    def __init__(self,tracer=None):self.tracer=tracer or Tracer();self.prefix="subsystem_77"
    def name(self,key):return f"{self.prefix}.{key}"
    def span(self,key,**kw):return self.tracer.span(self.name(key),**kw)
    def start(self,key,**kw):return self.tracer.start_span(self.name(key),**kw)
    def find(self,key):return self.tracer.find_by_name(self.name(key))
    def names(self):return sorted(set(s.name for s in self.tracer.spans() if s.name.startswith(self.prefix+".")))
    def count(self):return len([s for s in self.tracer.spans() if s.name.startswith(self.prefix+".")])
    def errors(self):return [s for s in self.tracer.spans() if s.name.startswith(self.prefix+".") and s.status=="error"]
    def durations(self):return [s.duration_ms for s in self.tracer.spans() if s.name.startswith(self.prefix+".") and s.duration_ms is not None]
    def average_duration(self):
        v=self.durations();return sum(v)/len(v) if v else 0


class TraceDomain78:
    """Trace namespace for subsystem 78."""
    def __init__(self,tracer=None):self.tracer=tracer or Tracer();self.prefix="subsystem_78"
    def name(self,key):return f"{self.prefix}.{key}"
    def span(self,key,**kw):return self.tracer.span(self.name(key),**kw)
    def start(self,key,**kw):return self.tracer.start_span(self.name(key),**kw)
    def find(self,key):return self.tracer.find_by_name(self.name(key))
    def names(self):return sorted(set(s.name for s in self.tracer.spans() if s.name.startswith(self.prefix+".")))
    def count(self):return len([s for s in self.tracer.spans() if s.name.startswith(self.prefix+".")])
    def errors(self):return [s for s in self.tracer.spans() if s.name.startswith(self.prefix+".") and s.status=="error"]
    def durations(self):return [s.duration_ms for s in self.tracer.spans() if s.name.startswith(self.prefix+".") and s.duration_ms is not None]
    def average_duration(self):
        v=self.durations();return sum(v)/len(v) if v else 0


class TraceDomain79:
    """Trace namespace for subsystem 79."""
    def __init__(self,tracer=None):self.tracer=tracer or Tracer();self.prefix="subsystem_79"
    def name(self,key):return f"{self.prefix}.{key}"
    def span(self,key,**kw):return self.tracer.span(self.name(key),**kw)
    def start(self,key,**kw):return self.tracer.start_span(self.name(key),**kw)
    def find(self,key):return self.tracer.find_by_name(self.name(key))
    def names(self):return sorted(set(s.name for s in self.tracer.spans() if s.name.startswith(self.prefix+".")))
    def count(self):return len([s for s in self.tracer.spans() if s.name.startswith(self.prefix+".")])
    def errors(self):return [s for s in self.tracer.spans() if s.name.startswith(self.prefix+".") and s.status=="error"]
    def durations(self):return [s.duration_ms for s in self.tracer.spans() if s.name.startswith(self.prefix+".") and s.duration_ms is not None]
    def average_duration(self):
        v=self.durations();return sum(v)/len(v) if v else 0


class TraceDomain80:
    """Trace namespace for subsystem 80."""
    def __init__(self,tracer=None):self.tracer=tracer or Tracer();self.prefix="subsystem_80"
    def name(self,key):return f"{self.prefix}.{key}"
    def span(self,key,**kw):return self.tracer.span(self.name(key),**kw)
    def start(self,key,**kw):return self.tracer.start_span(self.name(key),**kw)
    def find(self,key):return self.tracer.find_by_name(self.name(key))
    def names(self):return sorted(set(s.name for s in self.tracer.spans() if s.name.startswith(self.prefix+".")))
    def count(self):return len([s for s in self.tracer.spans() if s.name.startswith(self.prefix+".")])
    def errors(self):return [s for s in self.tracer.spans() if s.name.startswith(self.prefix+".") and s.status=="error"]
    def durations(self):return [s.duration_ms for s in self.tracer.spans() if s.name.startswith(self.prefix+".") and s.duration_ms is not None]
    def average_duration(self):
        v=self.durations();return sum(v)/len(v) if v else 0


class TraceDomain81:
    """Trace namespace for subsystem 81."""
    def __init__(self,tracer=None):self.tracer=tracer or Tracer();self.prefix="subsystem_81"
    def name(self,key):return f"{self.prefix}.{key}"
    def span(self,key,**kw):return self.tracer.span(self.name(key),**kw)
    def start(self,key,**kw):return self.tracer.start_span(self.name(key),**kw)
    def find(self,key):return self.tracer.find_by_name(self.name(key))
    def names(self):return sorted(set(s.name for s in self.tracer.spans() if s.name.startswith(self.prefix+".")))
    def count(self):return len([s for s in self.tracer.spans() if s.name.startswith(self.prefix+".")])
    def errors(self):return [s for s in self.tracer.spans() if s.name.startswith(self.prefix+".") and s.status=="error"]
    def durations(self):return [s.duration_ms for s in self.tracer.spans() if s.name.startswith(self.prefix+".") and s.duration_ms is not None]
    def average_duration(self):
        v=self.durations();return sum(v)/len(v) if v else 0


class TraceDomain82:
    """Trace namespace for subsystem 82."""
    def __init__(self,tracer=None):self.tracer=tracer or Tracer();self.prefix="subsystem_82"
    def name(self,key):return f"{self.prefix}.{key}"
    def span(self,key,**kw):return self.tracer.span(self.name(key),**kw)
    def start(self,key,**kw):return self.tracer.start_span(self.name(key),**kw)
    def find(self,key):return self.tracer.find_by_name(self.name(key))
    def names(self):return sorted(set(s.name for s in self.tracer.spans() if s.name.startswith(self.prefix+".")))
    def count(self):return len([s for s in self.tracer.spans() if s.name.startswith(self.prefix+".")])
    def errors(self):return [s for s in self.tracer.spans() if s.name.startswith(self.prefix+".") and s.status=="error"]
    def durations(self):return [s.duration_ms for s in self.tracer.spans() if s.name.startswith(self.prefix+".") and s.duration_ms is not None]
    def average_duration(self):
        v=self.durations();return sum(v)/len(v) if v else 0


class TraceDomain83:
    """Trace namespace for subsystem 83."""
    def __init__(self,tracer=None):self.tracer=tracer or Tracer();self.prefix="subsystem_83"
    def name(self,key):return f"{self.prefix}.{key}"
    def span(self,key,**kw):return self.tracer.span(self.name(key),**kw)
    def start(self,key,**kw):return self.tracer.start_span(self.name(key),**kw)
    def find(self,key):return self.tracer.find_by_name(self.name(key))
    def names(self):return sorted(set(s.name for s in self.tracer.spans() if s.name.startswith(self.prefix+".")))
    def count(self):return len([s for s in self.tracer.spans() if s.name.startswith(self.prefix+".")])
    def errors(self):return [s for s in self.tracer.spans() if s.name.startswith(self.prefix+".") and s.status=="error"]
    def durations(self):return [s.duration_ms for s in self.tracer.spans() if s.name.startswith(self.prefix+".") and s.duration_ms is not None]
    def average_duration(self):
        v=self.durations();return sum(v)/len(v) if v else 0


class TraceDomain84:
    """Trace namespace for subsystem 84."""
    def __init__(self,tracer=None):self.tracer=tracer or Tracer();self.prefix="subsystem_84"
    def name(self,key):return f"{self.prefix}.{key}"
    def span(self,key,**kw):return self.tracer.span(self.name(key),**kw)
    def start(self,key,**kw):return self.tracer.start_span(self.name(key),**kw)
    def find(self,key):return self.tracer.find_by_name(self.name(key))
    def names(self):return sorted(set(s.name for s in self.tracer.spans() if s.name.startswith(self.prefix+".")))
    def count(self):return len([s for s in self.tracer.spans() if s.name.startswith(self.prefix+".")])
    def errors(self):return [s for s in self.tracer.spans() if s.name.startswith(self.prefix+".") and s.status=="error"]
    def durations(self):return [s.duration_ms for s in self.tracer.spans() if s.name.startswith(self.prefix+".") and s.duration_ms is not None]
    def average_duration(self):
        v=self.durations();return sum(v)/len(v) if v else 0


class TraceDomain85:
    """Trace namespace for subsystem 85."""
    def __init__(self,tracer=None):self.tracer=tracer or Tracer();self.prefix="subsystem_85"
    def name(self,key):return f"{self.prefix}.{key}"
    def span(self,key,**kw):return self.tracer.span(self.name(key),**kw)
    def start(self,key,**kw):return self.tracer.start_span(self.name(key),**kw)
    def find(self,key):return self.tracer.find_by_name(self.name(key))
    def names(self):return sorted(set(s.name for s in self.tracer.spans() if s.name.startswith(self.prefix+".")))
    def count(self):return len([s for s in self.tracer.spans() if s.name.startswith(self.prefix+".")])
    def errors(self):return [s for s in self.tracer.spans() if s.name.startswith(self.prefix+".") and s.status=="error"]
    def durations(self):return [s.duration_ms for s in self.tracer.spans() if s.name.startswith(self.prefix+".") and s.duration_ms is not None]
    def average_duration(self):
        v=self.durations();return sum(v)/len(v) if v else 0


class TraceDomain86:
    """Trace namespace for subsystem 86."""
    def __init__(self,tracer=None):self.tracer=tracer or Tracer();self.prefix="subsystem_86"
    def name(self,key):return f"{self.prefix}.{key}"
    def span(self,key,**kw):return self.tracer.span(self.name(key),**kw)
    def start(self,key,**kw):return self.tracer.start_span(self.name(key),**kw)
    def find(self,key):return self.tracer.find_by_name(self.name(key))
    def names(self):return sorted(set(s.name for s in self.tracer.spans() if s.name.startswith(self.prefix+".")))
    def count(self):return len([s for s in self.tracer.spans() if s.name.startswith(self.prefix+".")])
    def errors(self):return [s for s in self.tracer.spans() if s.name.startswith(self.prefix+".") and s.status=="error"]
    def durations(self):return [s.duration_ms for s in self.tracer.spans() if s.name.startswith(self.prefix+".") and s.duration_ms is not None]
    def average_duration(self):
        v=self.durations();return sum(v)/len(v) if v else 0


class TraceDomain87:
    """Trace namespace for subsystem 87."""
    def __init__(self,tracer=None):self.tracer=tracer or Tracer();self.prefix="subsystem_87"
    def name(self,key):return f"{self.prefix}.{key}"
    def span(self,key,**kw):return self.tracer.span(self.name(key),**kw)
    def start(self,key,**kw):return self.tracer.start_span(self.name(key),**kw)
    def find(self,key):return self.tracer.find_by_name(self.name(key))
    def names(self):return sorted(set(s.name for s in self.tracer.spans() if s.name.startswith(self.prefix+".")))
    def count(self):return len([s for s in self.tracer.spans() if s.name.startswith(self.prefix+".")])
    def errors(self):return [s for s in self.tracer.spans() if s.name.startswith(self.prefix+".") and s.status=="error"]
    def durations(self):return [s.duration_ms for s in self.tracer.spans() if s.name.startswith(self.prefix+".") and s.duration_ms is not None]
    def average_duration(self):
        v=self.durations();return sum(v)/len(v) if v else 0


class TraceDomain88:
    """Trace namespace for subsystem 88."""
    def __init__(self,tracer=None):self.tracer=tracer or Tracer();self.prefix="subsystem_88"
    def name(self,key):return f"{self.prefix}.{key}"
    def span(self,key,**kw):return self.tracer.span(self.name(key),**kw)
    def start(self,key,**kw):return self.tracer.start_span(self.name(key),**kw)
    def find(self,key):return self.tracer.find_by_name(self.name(key))
    def names(self):return sorted(set(s.name for s in self.tracer.spans() if s.name.startswith(self.prefix+".")))
    def count(self):return len([s for s in self.tracer.spans() if s.name.startswith(self.prefix+".")])
    def errors(self):return [s for s in self.tracer.spans() if s.name.startswith(self.prefix+".") and s.status=="error"]
    def durations(self):return [s.duration_ms for s in self.tracer.spans() if s.name.startswith(self.prefix+".") and s.duration_ms is not None]
    def average_duration(self):
        v=self.durations();return sum(v)/len(v) if v else 0


class TraceDomain89:
    """Trace namespace for subsystem 89."""
    def __init__(self,tracer=None):self.tracer=tracer or Tracer();self.prefix="subsystem_89"
    def name(self,key):return f"{self.prefix}.{key}"
    def span(self,key,**kw):return self.tracer.span(self.name(key),**kw)
    def start(self,key,**kw):return self.tracer.start_span(self.name(key),**kw)
    def find(self,key):return self.tracer.find_by_name(self.name(key))
    def names(self):return sorted(set(s.name for s in self.tracer.spans() if s.name.startswith(self.prefix+".")))
    def count(self):return len([s for s in self.tracer.spans() if s.name.startswith(self.prefix+".")])
    def errors(self):return [s for s in self.tracer.spans() if s.name.startswith(self.prefix+".") and s.status=="error"]
    def durations(self):return [s.duration_ms for s in self.tracer.spans() if s.name.startswith(self.prefix+".") and s.duration_ms is not None]
    def average_duration(self):
        v=self.durations();return sum(v)/len(v) if v else 0


class TraceDomain90:
    """Trace namespace for subsystem 90."""
    def __init__(self,tracer=None):self.tracer=tracer or Tracer();self.prefix="subsystem_90"
    def name(self,key):return f"{self.prefix}.{key}"
    def span(self,key,**kw):return self.tracer.span(self.name(key),**kw)
    def start(self,key,**kw):return self.tracer.start_span(self.name(key),**kw)
    def find(self,key):return self.tracer.find_by_name(self.name(key))
    def names(self):return sorted(set(s.name for s in self.tracer.spans() if s.name.startswith(self.prefix+".")))
    def count(self):return len([s for s in self.tracer.spans() if s.name.startswith(self.prefix+".")])
    def errors(self):return [s for s in self.tracer.spans() if s.name.startswith(self.prefix+".") and s.status=="error"]
    def durations(self):return [s.duration_ms for s in self.tracer.spans() if s.name.startswith(self.prefix+".") and s.duration_ms is not None]
    def average_duration(self):
        v=self.durations();return sum(v)/len(v) if v else 0


class TraceDomain91:
    """Trace namespace for subsystem 91."""
    def __init__(self,tracer=None):self.tracer=tracer or Tracer();self.prefix="subsystem_91"
    def name(self,key):return f"{self.prefix}.{key}"
    def span(self,key,**kw):return self.tracer.span(self.name(key),**kw)
    def start(self,key,**kw):return self.tracer.start_span(self.name(key),**kw)
    def find(self,key):return self.tracer.find_by_name(self.name(key))
    def names(self):return sorted(set(s.name for s in self.tracer.spans() if s.name.startswith(self.prefix+".")))
    def count(self):return len([s for s in self.tracer.spans() if s.name.startswith(self.prefix+".")])
    def errors(self):return [s for s in self.tracer.spans() if s.name.startswith(self.prefix+".") and s.status=="error"]
    def durations(self):return [s.duration_ms for s in self.tracer.spans() if s.name.startswith(self.prefix+".") and s.duration_ms is not None]
    def average_duration(self):
        v=self.durations();return sum(v)/len(v) if v else 0


class TraceDomain92:
    """Trace namespace for subsystem 92."""
    def __init__(self,tracer=None):self.tracer=tracer or Tracer();self.prefix="subsystem_92"
    def name(self,key):return f"{self.prefix}.{key}"
    def span(self,key,**kw):return self.tracer.span(self.name(key),**kw)
    def start(self,key,**kw):return self.tracer.start_span(self.name(key),**kw)
    def find(self,key):return self.tracer.find_by_name(self.name(key))
    def names(self):return sorted(set(s.name for s in self.tracer.spans() if s.name.startswith(self.prefix+".")))
    def count(self):return len([s for s in self.tracer.spans() if s.name.startswith(self.prefix+".")])
    def errors(self):return [s for s in self.tracer.spans() if s.name.startswith(self.prefix+".") and s.status=="error"]
    def durations(self):return [s.duration_ms for s in self.tracer.spans() if s.name.startswith(self.prefix+".") and s.duration_ms is not None]
    def average_duration(self):
        v=self.durations();return sum(v)/len(v) if v else 0


class TraceDomain93:
    """Trace namespace for subsystem 93."""
    def __init__(self,tracer=None):self.tracer=tracer or Tracer();self.prefix="subsystem_93"
    def name(self,key):return f"{self.prefix}.{key}"
    def span(self,key,**kw):return self.tracer.span(self.name(key),**kw)
    def start(self,key,**kw):return self.tracer.start_span(self.name(key),**kw)
    def find(self,key):return self.tracer.find_by_name(self.name(key))
    def names(self):return sorted(set(s.name for s in self.tracer.spans() if s.name.startswith(self.prefix+".")))
    def count(self):return len([s for s in self.tracer.spans() if s.name.startswith(self.prefix+".")])
    def errors(self):return [s for s in self.tracer.spans() if s.name.startswith(self.prefix+".") and s.status=="error"]
    def durations(self):return [s.duration_ms for s in self.tracer.spans() if s.name.startswith(self.prefix+".") and s.duration_ms is not None]
    def average_duration(self):
        v=self.durations();return sum(v)/len(v) if v else 0


class TraceDomain94:
    """Trace namespace for subsystem 94."""
    def __init__(self,tracer=None):self.tracer=tracer or Tracer();self.prefix="subsystem_94"
    def name(self,key):return f"{self.prefix}.{key}"
    def span(self,key,**kw):return self.tracer.span(self.name(key),**kw)
    def start(self,key,**kw):return self.tracer.start_span(self.name(key),**kw)
    def find(self,key):return self.tracer.find_by_name(self.name(key))
    def names(self):return sorted(set(s.name for s in self.tracer.spans() if s.name.startswith(self.prefix+".")))
    def count(self):return len([s for s in self.tracer.spans() if s.name.startswith(self.prefix+".")])
    def errors(self):return [s for s in self.tracer.spans() if s.name.startswith(self.prefix+".") and s.status=="error"]
    def durations(self):return [s.duration_ms for s in self.tracer.spans() if s.name.startswith(self.prefix+".") and s.duration_ms is not None]
    def average_duration(self):
        v=self.durations();return sum(v)/len(v) if v else 0


class TraceDomain95:
    """Trace namespace for subsystem 95."""
    def __init__(self,tracer=None):self.tracer=tracer or Tracer();self.prefix="subsystem_95"
    def name(self,key):return f"{self.prefix}.{key}"
    def span(self,key,**kw):return self.tracer.span(self.name(key),**kw)
    def start(self,key,**kw):return self.tracer.start_span(self.name(key),**kw)
    def find(self,key):return self.tracer.find_by_name(self.name(key))
    def names(self):return sorted(set(s.name for s in self.tracer.spans() if s.name.startswith(self.prefix+".")))
    def count(self):return len([s for s in self.tracer.spans() if s.name.startswith(self.prefix+".")])
    def errors(self):return [s for s in self.tracer.spans() if s.name.startswith(self.prefix+".") and s.status=="error"]
    def durations(self):return [s.duration_ms for s in self.tracer.spans() if s.name.startswith(self.prefix+".") and s.duration_ms is not None]
    def average_duration(self):
        v=self.durations();return sum(v)/len(v) if v else 0


class TraceDomain96:
    """Trace namespace for subsystem 96."""
    def __init__(self,tracer=None):self.tracer=tracer or Tracer();self.prefix="subsystem_96"
    def name(self,key):return f"{self.prefix}.{key}"
    def span(self,key,**kw):return self.tracer.span(self.name(key),**kw)
    def start(self,key,**kw):return self.tracer.start_span(self.name(key),**kw)
    def find(self,key):return self.tracer.find_by_name(self.name(key))
    def names(self):return sorted(set(s.name for s in self.tracer.spans() if s.name.startswith(self.prefix+".")))
    def count(self):return len([s for s in self.tracer.spans() if s.name.startswith(self.prefix+".")])
    def errors(self):return [s for s in self.tracer.spans() if s.name.startswith(self.prefix+".") and s.status=="error"]
    def durations(self):return [s.duration_ms for s in self.tracer.spans() if s.name.startswith(self.prefix+".") and s.duration_ms is not None]
    def average_duration(self):
        v=self.durations();return sum(v)/len(v) if v else 0


class TraceDomain97:
    """Trace namespace for subsystem 97."""
    def __init__(self,tracer=None):self.tracer=tracer or Tracer();self.prefix="subsystem_97"
    def name(self,key):return f"{self.prefix}.{key}"
    def span(self,key,**kw):return self.tracer.span(self.name(key),**kw)
    def start(self,key,**kw):return self.tracer.start_span(self.name(key),**kw)
    def find(self,key):return self.tracer.find_by_name(self.name(key))
    def names(self):return sorted(set(s.name for s in self.tracer.spans() if s.name.startswith(self.prefix+".")))
    def count(self):return len([s for s in self.tracer.spans() if s.name.startswith(self.prefix+".")])
    def errors(self):return [s for s in self.tracer.spans() if s.name.startswith(self.prefix+".") and s.status=="error"]
    def durations(self):return [s.duration_ms for s in self.tracer.spans() if s.name.startswith(self.prefix+".") and s.duration_ms is not None]
    def average_duration(self):
        v=self.durations();return sum(v)/len(v) if v else 0


class TraceDomain98:
    """Trace namespace for subsystem 98."""
    def __init__(self,tracer=None):self.tracer=tracer or Tracer();self.prefix="subsystem_98"
    def name(self,key):return f"{self.prefix}.{key}"
    def span(self,key,**kw):return self.tracer.span(self.name(key),**kw)
    def start(self,key,**kw):return self.tracer.start_span(self.name(key),**kw)
    def find(self,key):return self.tracer.find_by_name(self.name(key))
    def names(self):return sorted(set(s.name for s in self.tracer.spans() if s.name.startswith(self.prefix+".")))
    def count(self):return len([s for s in self.tracer.spans() if s.name.startswith(self.prefix+".")])
    def errors(self):return [s for s in self.tracer.spans() if s.name.startswith(self.prefix+".") and s.status=="error"]
    def durations(self):return [s.duration_ms for s in self.tracer.spans() if s.name.startswith(self.prefix+".") and s.duration_ms is not None]
    def average_duration(self):
        v=self.durations();return sum(v)/len(v) if v else 0


class TraceDomain99:
    """Trace namespace for subsystem 99."""
    def __init__(self,tracer=None):self.tracer=tracer or Tracer();self.prefix="subsystem_99"
    def name(self,key):return f"{self.prefix}.{key}"
    def span(self,key,**kw):return self.tracer.span(self.name(key),**kw)
    def start(self,key,**kw):return self.tracer.start_span(self.name(key),**kw)
    def find(self,key):return self.tracer.find_by_name(self.name(key))
    def names(self):return sorted(set(s.name for s in self.tracer.spans() if s.name.startswith(self.prefix+".")))
    def count(self):return len([s for s in self.tracer.spans() if s.name.startswith(self.prefix+".")])
    def errors(self):return [s for s in self.tracer.spans() if s.name.startswith(self.prefix+".") and s.status=="error"]
    def durations(self):return [s.duration_ms for s in self.tracer.spans() if s.name.startswith(self.prefix+".") and s.duration_ms is not None]
    def average_duration(self):
        v=self.durations();return sum(v)/len(v) if v else 0


class TraceDomain100:
    """Trace namespace for subsystem 100."""
    def __init__(self,tracer=None):self.tracer=tracer or Tracer();self.prefix="subsystem_100"
    def name(self,key):return f"{self.prefix}.{key}"
    def span(self,key,**kw):return self.tracer.span(self.name(key),**kw)
    def start(self,key,**kw):return self.tracer.start_span(self.name(key),**kw)
    def find(self,key):return self.tracer.find_by_name(self.name(key))
    def names(self):return sorted(set(s.name for s in self.tracer.spans() if s.name.startswith(self.prefix+".")))
    def count(self):return len([s for s in self.tracer.spans() if s.name.startswith(self.prefix+".")])
    def errors(self):return [s for s in self.tracer.spans() if s.name.startswith(self.prefix+".") and s.status=="error"]
    def durations(self):return [s.duration_ms for s in self.tracer.spans() if s.name.startswith(self.prefix+".") and s.duration_ms is not None]
    def average_duration(self):
        v=self.durations();return sum(v)/len(v) if v else 0


class TraceDomain101:
    """Trace namespace for subsystem 101."""
    def __init__(self,tracer=None):self.tracer=tracer or Tracer();self.prefix="subsystem_101"
    def name(self,key):return f"{self.prefix}.{key}"
    def span(self,key,**kw):return self.tracer.span(self.name(key),**kw)
    def start(self,key,**kw):return self.tracer.start_span(self.name(key),**kw)
    def find(self,key):return self.tracer.find_by_name(self.name(key))
    def names(self):return sorted(set(s.name for s in self.tracer.spans() if s.name.startswith(self.prefix+".")))
    def count(self):return len([s for s in self.tracer.spans() if s.name.startswith(self.prefix+".")])
    def errors(self):return [s for s in self.tracer.spans() if s.name.startswith(self.prefix+".") and s.status=="error"]
    def durations(self):return [s.duration_ms for s in self.tracer.spans() if s.name.startswith(self.prefix+".") and s.duration_ms is not None]
    def average_duration(self):
        v=self.durations();return sum(v)/len(v) if v else 0


class TraceDomain102:
    """Trace namespace for subsystem 102."""
    def __init__(self,tracer=None):self.tracer=tracer or Tracer();self.prefix="subsystem_102"
    def name(self,key):return f"{self.prefix}.{key}"
    def span(self,key,**kw):return self.tracer.span(self.name(key),**kw)
    def start(self,key,**kw):return self.tracer.start_span(self.name(key),**kw)
    def find(self,key):return self.tracer.find_by_name(self.name(key))
    def names(self):return sorted(set(s.name for s in self.tracer.spans() if s.name.startswith(self.prefix+".")))
    def count(self):return len([s for s in self.tracer.spans() if s.name.startswith(self.prefix+".")])
    def errors(self):return [s for s in self.tracer.spans() if s.name.startswith(self.prefix+".") and s.status=="error"]
    def durations(self):return [s.duration_ms for s in self.tracer.spans() if s.name.startswith(self.prefix+".") and s.duration_ms is not None]
    def average_duration(self):
        v=self.durations();return sum(v)/len(v) if v else 0


class TraceDomain103:
    """Trace namespace for subsystem 103."""
    def __init__(self,tracer=None):self.tracer=tracer or Tracer();self.prefix="subsystem_103"
    def name(self,key):return f"{self.prefix}.{key}"
    def span(self,key,**kw):return self.tracer.span(self.name(key),**kw)
    def start(self,key,**kw):return self.tracer.start_span(self.name(key),**kw)
    def find(self,key):return self.tracer.find_by_name(self.name(key))
    def names(self):return sorted(set(s.name for s in self.tracer.spans() if s.name.startswith(self.prefix+".")))
    def count(self):return len([s for s in self.tracer.spans() if s.name.startswith(self.prefix+".")])
    def errors(self):return [s for s in self.tracer.spans() if s.name.startswith(self.prefix+".") and s.status=="error"]
    def durations(self):return [s.duration_ms for s in self.tracer.spans() if s.name.startswith(self.prefix+".") and s.duration_ms is not None]
    def average_duration(self):
        v=self.durations();return sum(v)/len(v) if v else 0


class TraceDomain104:
    """Trace namespace for subsystem 104."""
    def __init__(self,tracer=None):self.tracer=tracer or Tracer();self.prefix="subsystem_104"
    def name(self,key):return f"{self.prefix}.{key}"
    def span(self,key,**kw):return self.tracer.span(self.name(key),**kw)
    def start(self,key,**kw):return self.tracer.start_span(self.name(key),**kw)
    def find(self,key):return self.tracer.find_by_name(self.name(key))
    def names(self):return sorted(set(s.name for s in self.tracer.spans() if s.name.startswith(self.prefix+".")))
    def count(self):return len([s for s in self.tracer.spans() if s.name.startswith(self.prefix+".")])
    def errors(self):return [s for s in self.tracer.spans() if s.name.startswith(self.prefix+".") and s.status=="error"]
    def durations(self):return [s.duration_ms for s in self.tracer.spans() if s.name.startswith(self.prefix+".") and s.duration_ms is not None]
    def average_duration(self):
        v=self.durations();return sum(v)/len(v) if v else 0


class TraceDomain105:
    """Trace namespace for subsystem 105."""
    def __init__(self,tracer=None):self.tracer=tracer or Tracer();self.prefix="subsystem_105"
    def name(self,key):return f"{self.prefix}.{key}"
    def span(self,key,**kw):return self.tracer.span(self.name(key),**kw)
    def start(self,key,**kw):return self.tracer.start_span(self.name(key),**kw)
    def find(self,key):return self.tracer.find_by_name(self.name(key))
    def names(self):return sorted(set(s.name for s in self.tracer.spans() if s.name.startswith(self.prefix+".")))
    def count(self):return len([s for s in self.tracer.spans() if s.name.startswith(self.prefix+".")])
    def errors(self):return [s for s in self.tracer.spans() if s.name.startswith(self.prefix+".") and s.status=="error"]
    def durations(self):return [s.duration_ms for s in self.tracer.spans() if s.name.startswith(self.prefix+".") and s.duration_ms is not None]
    def average_duration(self):
        v=self.durations();return sum(v)/len(v) if v else 0


class TraceDomain106:
    """Trace namespace for subsystem 106."""
    def __init__(self,tracer=None):self.tracer=tracer or Tracer();self.prefix="subsystem_106"
    def name(self,key):return f"{self.prefix}.{key}"
    def span(self,key,**kw):return self.tracer.span(self.name(key),**kw)
    def start(self,key,**kw):return self.tracer.start_span(self.name(key),**kw)
    def find(self,key):return self.tracer.find_by_name(self.name(key))
    def names(self):return sorted(set(s.name for s in self.tracer.spans() if s.name.startswith(self.prefix+".")))
    def count(self):return len([s for s in self.tracer.spans() if s.name.startswith(self.prefix+".")])
    def errors(self):return [s for s in self.tracer.spans() if s.name.startswith(self.prefix+".") and s.status=="error"]
    def durations(self):return [s.duration_ms for s in self.tracer.spans() if s.name.startswith(self.prefix+".") and s.duration_ms is not None]
    def average_duration(self):
        v=self.durations();return sum(v)/len(v) if v else 0


class TraceDomain107:
    """Trace namespace for subsystem 107."""
    def __init__(self,tracer=None):self.tracer=tracer or Tracer();self.prefix="subsystem_107"
    def name(self,key):return f"{self.prefix}.{key}"
    def span(self,key,**kw):return self.tracer.span(self.name(key),**kw)
    def start(self,key,**kw):return self.tracer.start_span(self.name(key),**kw)
    def find(self,key):return self.tracer.find_by_name(self.name(key))
    def names(self):return sorted(set(s.name for s in self.tracer.spans() if s.name.startswith(self.prefix+".")))
    def count(self):return len([s for s in self.tracer.spans() if s.name.startswith(self.prefix+".")])
    def errors(self):return [s for s in self.tracer.spans() if s.name.startswith(self.prefix+".") and s.status=="error"]
    def durations(self):return [s.duration_ms for s in self.tracer.spans() if s.name.startswith(self.prefix+".") and s.duration_ms is not None]
    def average_duration(self):
        v=self.durations();return sum(v)/len(v) if v else 0


class TraceDomain108:
    """Trace namespace for subsystem 108."""
    def __init__(self,tracer=None):self.tracer=tracer or Tracer();self.prefix="subsystem_108"
    def name(self,key):return f"{self.prefix}.{key}"
    def span(self,key,**kw):return self.tracer.span(self.name(key),**kw)
    def start(self,key,**kw):return self.tracer.start_span(self.name(key),**kw)
    def find(self,key):return self.tracer.find_by_name(self.name(key))
    def names(self):return sorted(set(s.name for s in self.tracer.spans() if s.name.startswith(self.prefix+".")))
    def count(self):return len([s for s in self.tracer.spans() if s.name.startswith(self.prefix+".")])
    def errors(self):return [s for s in self.tracer.spans() if s.name.startswith(self.prefix+".") and s.status=="error"]
    def durations(self):return [s.duration_ms for s in self.tracer.spans() if s.name.startswith(self.prefix+".") and s.duration_ms is not None]
    def average_duration(self):
        v=self.durations();return sum(v)/len(v) if v else 0


class TraceDomain109:
    """Trace namespace for subsystem 109."""
    def __init__(self,tracer=None):self.tracer=tracer or Tracer();self.prefix="subsystem_109"
    def name(self,key):return f"{self.prefix}.{key}"
    def span(self,key,**kw):return self.tracer.span(self.name(key),**kw)
    def start(self,key,**kw):return self.tracer.start_span(self.name(key),**kw)
    def find(self,key):return self.tracer.find_by_name(self.name(key))
    def names(self):return sorted(set(s.name for s in self.tracer.spans() if s.name.startswith(self.prefix+".")))
    def count(self):return len([s for s in self.tracer.spans() if s.name.startswith(self.prefix+".")])
    def errors(self):return [s for s in self.tracer.spans() if s.name.startswith(self.prefix+".") and s.status=="error"]
    def durations(self):return [s.duration_ms for s in self.tracer.spans() if s.name.startswith(self.prefix+".") and s.duration_ms is not None]
    def average_duration(self):
        v=self.durations();return sum(v)/len(v) if v else 0


class TraceDomain110:
    """Trace namespace for subsystem 110."""
    def __init__(self,tracer=None):self.tracer=tracer or Tracer();self.prefix="subsystem_110"
    def name(self,key):return f"{self.prefix}.{key}"
    def span(self,key,**kw):return self.tracer.span(self.name(key),**kw)
    def start(self,key,**kw):return self.tracer.start_span(self.name(key),**kw)
    def find(self,key):return self.tracer.find_by_name(self.name(key))
    def names(self):return sorted(set(s.name for s in self.tracer.spans() if s.name.startswith(self.prefix+".")))
    def count(self):return len([s for s in self.tracer.spans() if s.name.startswith(self.prefix+".")])
    def errors(self):return [s for s in self.tracer.spans() if s.name.startswith(self.prefix+".") and s.status=="error"]
    def durations(self):return [s.duration_ms for s in self.tracer.spans() if s.name.startswith(self.prefix+".") and s.duration_ms is not None]
    def average_duration(self):
        v=self.durations();return sum(v)/len(v) if v else 0


class TraceDomain111:
    """Trace namespace for subsystem 111."""
    def __init__(self,tracer=None):self.tracer=tracer or Tracer();self.prefix="subsystem_111"
    def name(self,key):return f"{self.prefix}.{key}"
    def span(self,key,**kw):return self.tracer.span(self.name(key),**kw)
    def start(self,key,**kw):return self.tracer.start_span(self.name(key),**kw)
    def find(self,key):return self.tracer.find_by_name(self.name(key))
    def names(self):return sorted(set(s.name for s in self.tracer.spans() if s.name.startswith(self.prefix+".")))
    def count(self):return len([s for s in self.tracer.spans() if s.name.startswith(self.prefix+".")])
    def errors(self):return [s for s in self.tracer.spans() if s.name.startswith(self.prefix+".") and s.status=="error"]
    def durations(self):return [s.duration_ms for s in self.tracer.spans() if s.name.startswith(self.prefix+".") and s.duration_ms is not None]
    def average_duration(self):
        v=self.durations();return sum(v)/len(v) if v else 0


class TraceDomain112:
    """Trace namespace for subsystem 112."""
    def __init__(self,tracer=None):self.tracer=tracer or Tracer();self.prefix="subsystem_112"
    def name(self,key):return f"{self.prefix}.{key}"
    def span(self,key,**kw):return self.tracer.span(self.name(key),**kw)
    def start(self,key,**kw):return self.tracer.start_span(self.name(key),**kw)
    def find(self,key):return self.tracer.find_by_name(self.name(key))
    def names(self):return sorted(set(s.name for s in self.tracer.spans() if s.name.startswith(self.prefix+".")))
    def count(self):return len([s for s in self.tracer.spans() if s.name.startswith(self.prefix+".")])
    def errors(self):return [s for s in self.tracer.spans() if s.name.startswith(self.prefix+".") and s.status=="error"]
    def durations(self):return [s.duration_ms for s in self.tracer.spans() if s.name.startswith(self.prefix+".") and s.duration_ms is not None]
    def average_duration(self):
        v=self.durations();return sum(v)/len(v) if v else 0


class TraceDomain113:
    """Trace namespace for subsystem 113."""
    def __init__(self,tracer=None):self.tracer=tracer or Tracer();self.prefix="subsystem_113"
    def name(self,key):return f"{self.prefix}.{key}"
    def span(self,key,**kw):return self.tracer.span(self.name(key),**kw)
    def start(self,key,**kw):return self.tracer.start_span(self.name(key),**kw)
    def find(self,key):return self.tracer.find_by_name(self.name(key))
    def names(self):return sorted(set(s.name for s in self.tracer.spans() if s.name.startswith(self.prefix+".")))
    def count(self):return len([s for s in self.tracer.spans() if s.name.startswith(self.prefix+".")])
    def errors(self):return [s for s in self.tracer.spans() if s.name.startswith(self.prefix+".") and s.status=="error"]
    def durations(self):return [s.duration_ms for s in self.tracer.spans() if s.name.startswith(self.prefix+".") and s.duration_ms is not None]
    def average_duration(self):
        v=self.durations();return sum(v)/len(v) if v else 0


class TraceDomain114:
    """Trace namespace for subsystem 114."""
    def __init__(self,tracer=None):self.tracer=tracer or Tracer();self.prefix="subsystem_114"
    def name(self,key):return f"{self.prefix}.{key}"
    def span(self,key,**kw):return self.tracer.span(self.name(key),**kw)
    def start(self,key,**kw):return self.tracer.start_span(self.name(key),**kw)
    def find(self,key):return self.tracer.find_by_name(self.name(key))
    def names(self):return sorted(set(s.name for s in self.tracer.spans() if s.name.startswith(self.prefix+".")))
    def count(self):return len([s for s in self.tracer.spans() if s.name.startswith(self.prefix+".")])
    def errors(self):return [s for s in self.tracer.spans() if s.name.startswith(self.prefix+".") and s.status=="error"]
    def durations(self):return [s.duration_ms for s in self.tracer.spans() if s.name.startswith(self.prefix+".") and s.duration_ms is not None]
    def average_duration(self):
        v=self.durations();return sum(v)/len(v) if v else 0


class TraceDomain115:
    """Trace namespace for subsystem 115."""
    def __init__(self,tracer=None):self.tracer=tracer or Tracer();self.prefix="subsystem_115"
    def name(self,key):return f"{self.prefix}.{key}"
    def span(self,key,**kw):return self.tracer.span(self.name(key),**kw)
    def start(self,key,**kw):return self.tracer.start_span(self.name(key),**kw)
    def find(self,key):return self.tracer.find_by_name(self.name(key))
    def names(self):return sorted(set(s.name for s in self.tracer.spans() if s.name.startswith(self.prefix+".")))
    def count(self):return len([s for s in self.tracer.spans() if s.name.startswith(self.prefix+".")])
    def errors(self):return [s for s in self.tracer.spans() if s.name.startswith(self.prefix+".") and s.status=="error"]
    def durations(self):return [s.duration_ms for s in self.tracer.spans() if s.name.startswith(self.prefix+".") and s.duration_ms is not None]
    def average_duration(self):
        v=self.durations();return sum(v)/len(v) if v else 0


class TraceDomain116:
    """Trace namespace for subsystem 116."""
    def __init__(self,tracer=None):self.tracer=tracer or Tracer();self.prefix="subsystem_116"
    def name(self,key):return f"{self.prefix}.{key}"
    def span(self,key,**kw):return self.tracer.span(self.name(key),**kw)
    def start(self,key,**kw):return self.tracer.start_span(self.name(key),**kw)
    def find(self,key):return self.tracer.find_by_name(self.name(key))
    def names(self):return sorted(set(s.name for s in self.tracer.spans() if s.name.startswith(self.prefix+".")))
    def count(self):return len([s for s in self.tracer.spans() if s.name.startswith(self.prefix+".")])
    def errors(self):return [s for s in self.tracer.spans() if s.name.startswith(self.prefix+".") and s.status=="error"]
    def durations(self):return [s.duration_ms for s in self.tracer.spans() if s.name.startswith(self.prefix+".") and s.duration_ms is not None]
    def average_duration(self):
        v=self.durations();return sum(v)/len(v) if v else 0


class TraceDomain117:
    """Trace namespace for subsystem 117."""
    def __init__(self,tracer=None):self.tracer=tracer or Tracer();self.prefix="subsystem_117"
    def name(self,key):return f"{self.prefix}.{key}"
    def span(self,key,**kw):return self.tracer.span(self.name(key),**kw)
    def start(self,key,**kw):return self.tracer.start_span(self.name(key),**kw)
    def find(self,key):return self.tracer.find_by_name(self.name(key))
    def names(self):return sorted(set(s.name for s in self.tracer.spans() if s.name.startswith(self.prefix+".")))
    def count(self):return len([s for s in self.tracer.spans() if s.name.startswith(self.prefix+".")])
    def errors(self):return [s for s in self.tracer.spans() if s.name.startswith(self.prefix+".") and s.status=="error"]
    def durations(self):return [s.duration_ms for s in self.tracer.spans() if s.name.startswith(self.prefix+".") and s.duration_ms is not None]
    def average_duration(self):
        v=self.durations();return sum(v)/len(v) if v else 0


class TraceDomain118:
    """Trace namespace for subsystem 118."""
    def __init__(self,tracer=None):self.tracer=tracer or Tracer();self.prefix="subsystem_118"
    def name(self,key):return f"{self.prefix}.{key}"
    def span(self,key,**kw):return self.tracer.span(self.name(key),**kw)
    def start(self,key,**kw):return self.tracer.start_span(self.name(key),**kw)
    def find(self,key):return self.tracer.find_by_name(self.name(key))
    def names(self):return sorted(set(s.name for s in self.tracer.spans() if s.name.startswith(self.prefix+".")))
    def count(self):return len([s for s in self.tracer.spans() if s.name.startswith(self.prefix+".")])
    def errors(self):return [s for s in self.tracer.spans() if s.name.startswith(self.prefix+".") and s.status=="error"]
    def durations(self):return [s.duration_ms for s in self.tracer.spans() if s.name.startswith(self.prefix+".") and s.duration_ms is not None]
    def average_duration(self):
        v=self.durations();return sum(v)/len(v) if v else 0


class TraceDomain119:
    """Trace namespace for subsystem 119."""
    def __init__(self,tracer=None):self.tracer=tracer or Tracer();self.prefix="subsystem_119"
    def name(self,key):return f"{self.prefix}.{key}"
    def span(self,key,**kw):return self.tracer.span(self.name(key),**kw)
    def start(self,key,**kw):return self.tracer.start_span(self.name(key),**kw)
    def find(self,key):return self.tracer.find_by_name(self.name(key))
    def names(self):return sorted(set(s.name for s in self.tracer.spans() if s.name.startswith(self.prefix+".")))
    def count(self):return len([s for s in self.tracer.spans() if s.name.startswith(self.prefix+".")])
    def errors(self):return [s for s in self.tracer.spans() if s.name.startswith(self.prefix+".") and s.status=="error"]
    def durations(self):return [s.duration_ms for s in self.tracer.spans() if s.name.startswith(self.prefix+".") and s.duration_ms is not None]
    def average_duration(self):
        v=self.durations();return sum(v)/len(v) if v else 0


class TraceDomain120:
    """Trace namespace for subsystem 120."""
    def __init__(self,tracer=None):self.tracer=tracer or Tracer();self.prefix="subsystem_120"
    def name(self,key):return f"{self.prefix}.{key}"
    def span(self,key,**kw):return self.tracer.span(self.name(key),**kw)
    def start(self,key,**kw):return self.tracer.start_span(self.name(key),**kw)
    def find(self,key):return self.tracer.find_by_name(self.name(key))
    def names(self):return sorted(set(s.name for s in self.tracer.spans() if s.name.startswith(self.prefix+".")))
    def count(self):return len([s for s in self.tracer.spans() if s.name.startswith(self.prefix+".")])
    def errors(self):return [s for s in self.tracer.spans() if s.name.startswith(self.prefix+".") and s.status=="error"]
    def durations(self):return [s.duration_ms for s in self.tracer.spans() if s.name.startswith(self.prefix+".") and s.duration_ms is not None]
    def average_duration(self):
        v=self.durations();return sum(v)/len(v) if v else 0

__all__=[name for name in globals() if not name.startswith("_")]
