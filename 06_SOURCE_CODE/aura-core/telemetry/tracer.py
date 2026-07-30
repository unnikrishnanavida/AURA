from __future__ import annotations

from .span import Span


class Tracer:
    def start(self, name: str) -> Span:
        s = Span(name=name, meta={})
        s.start_span()
        return s
