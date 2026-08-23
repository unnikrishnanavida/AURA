from .span import Span
class Tracer:
    def __init__(self): self.spans=[]
    def start(self,name,attributes=None):
        span=Span(name,attributes=dict(attributes or {})); self.spans.append(span); return span
