from dataclasses import dataclass, field
from typing import Any

@dataclass(frozen=True, slots=True)
class GoalState:
    values: dict[str, Any] = field(default_factory=dict)
    required: frozenset[str] = frozenset()

    def matches(self, state) -> bool:
        actual = getattr(state, "values", state)
        return all(actual.get(k) == v for k, v in self.values.items()) and all(
            key in actual for key in self.required
        )

    def missing(self, state):
        actual = getattr(state, "values", state)
        return {k: v for k, v in self.values.items() if actual.get(k) != v}
