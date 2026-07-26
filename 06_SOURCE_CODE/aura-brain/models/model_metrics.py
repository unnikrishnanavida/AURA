"""Metrics model for models."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(slots=True)
class ModelMetrics:
    """Collects runtime metrics for model operations."""

    requests: int = 0
    failures: int = 0
    successes: int = 0
    latency_ms: list[int] = field(default_factory=list)

    def record_success(self, latency_ms: int | None = None) -> None:
        """Record a successful request."""
        self.requests += 1
        self.successes += 1
        if latency_ms is not None:
            self.latency_ms.append(latency_ms)

    def record_failure(self, latency_ms: int | None = None) -> None:
        """Record a failed request."""
        self.requests += 1
        self.failures += 1
        if latency_ms is not None:
            self.latency_ms.append(latency_ms)

    def success_rate(self) -> float:
        """Return the success rate as a percentage."""
        if self.requests == 0:
            return 0.0
        return self.successes / self.requests
