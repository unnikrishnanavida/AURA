"""Observation engine: records observed state from explicit sources.

Observations feed evaluation and recovery. The engine keeps an append-only
history per source; observers (tools, environment adapters, memory bridges)
never write to the engine directly -- they call ``observe``.
"""

from __future__ import annotations

from aura_agent.observation.models import Observation

__all__ = ["ObservationEngine"]


class ObservationEngine:
    def __init__(self) -> None:
        self._history: list[Observation] = []
        self._by_source: dict[str, list[Observation]] = {}

    def observe(
        self,
        *,
        source: str,
        state: dict,
        signals: list[str] | None = None,
        confidence: float = 1.0,
        execution_id=None,
        correlation_id: str | None = None,
        metadata: dict | None = None,
    ) -> Observation:
        obs = Observation(
            source=source,
            state=dict(state),
            signals=list(signals or []),
            confidence=confidence,
            execution_id=execution_id,
            correlation_id=correlation_id,
            metadata=dict(metadata or {}),
        )
        self._history.append(obs)
        self._by_source.setdefault(source, []).append(obs)
        return obs

    def latest(self, source: str | None = None) -> Observation | None:
        if source is None:
            return self._history[-1] if self._history else None
        bucket = self._by_source.get(source, [])
        return bucket[-1] if bucket else None

    def all(self) -> list[Observation]:
        return list(self._history)

    def by_source(self, source: str) -> list[Observation]:
        return list(self._by_source.get(source, []))

    def latest_state(self, source: str | None = None) -> dict:
        obs = self.latest(source)
        return dict(obs.state) if obs else {}

    def clear(self) -> None:
        self._history.clear()
        self._by_source.clear()