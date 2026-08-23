from .tracing.tracer import Tracer
class TelemetryEngine:
    def __init__(self,exporter=None):
        self.tracer=Tracer(); self.exporter=exporter
    def span(self,name,attributes=None):
        span=self.tracer.start(name,attributes)
        if self.exporter: self.exporter.export(span)
        return span
