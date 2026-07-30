from __future__ import annotations

from typing import Any


class Exporter:
    def export(self, metric_name: str, value: Any) -> None:
        # Hook point for pushing metrics to backends
        pass
