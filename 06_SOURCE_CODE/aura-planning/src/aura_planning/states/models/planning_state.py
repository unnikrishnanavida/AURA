from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any

@dataclass(frozen=True, slots=True)
class PlanningState:
    values: dict[str, Any] = field(default_factory=dict)
    version: int = 0
    timestamp: float | None = None

    def get(self, key, default=None): return self.values.get(key, default)
    def contains(self, key): return key in self.values

    def with_value(self, key, value):
        values = dict(self.values)
        values[key] = value
        return PlanningState(values, self.version + 1, self.timestamp)

    def with_values(self, updates):
        values = dict(self.values)
        values.update(updates)
        return PlanningState(values, self.version + 1, self.timestamp)

    def without(self, key):
        if key not in self.values: return self
        values = dict(self.values)
        del values[key]
        return PlanningState(values, self.version + 1, self.timestamp)

    def observable(self):
        return dict(self.values)
