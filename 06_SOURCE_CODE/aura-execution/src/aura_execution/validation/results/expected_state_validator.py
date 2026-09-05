"""Expected-state validator: verifies observed state matches declared effects."""

from __future__ import annotations

from typing import Any


class ExpectedStateValidator:
    """Compares declared effects against the observed post-execution state."""

    def compare(self, expected: dict[str, Any], observed: dict[str, Any]) -> tuple[bool, dict[str, Any]]:
        mismatches: dict[str, Any] = {}
        for key, expected_value in (expected or {}).items():
            if observed.get(key) != expected_value:
                mismatch = {"want": expected_value, "have": observed.get(key)}
                mismatches[key] = mismatch
        return (not mismatches, mismatches)


__all__ = ["ExpectedStateValidator"]