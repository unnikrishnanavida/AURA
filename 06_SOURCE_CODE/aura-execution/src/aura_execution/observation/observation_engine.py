"""Observation engine: diffs before/after execution state."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class Observation:
    """Recorded changes between the pre- and post-execution state."""

    changes: dict[str, Any] = field(default_factory=dict)

    def changed_keys(self) -> tuple[str, ...]:
        return tuple(self.changes.keys())


class ObservationEngine:
    """Produces the set of state changes an execution caused."""

    def observe(self, before: dict[str, Any], after: dict[str, Any]) -> Observation:
        changes: dict[str, Any] = {}
        all_keys = set(before) | set(after)
        for key in sorted(all_keys):
            before_val = before.get(key)
            after_val = after.get(key)
            if before_val != after_val:
                changes[key] = {"before": before_val, "after": after_val}
        return Observation(changes=changes)


__all__ = ["Observation", "ObservationEngine"]