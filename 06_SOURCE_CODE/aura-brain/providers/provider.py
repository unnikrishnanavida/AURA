"""Core provider abstraction with production-oriented lifecycle support."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from .provider_capability import ProviderCapability
from .provider_config import ProviderConfig
from .provider_health import ProviderHealth
from .provider_metrics import ProviderMetrics
from .provider_state import ProviderState, ProviderStatus
from .policy import RetryPolicy, TimeoutPolicy, CircuitBreaker
from typing import Callable


class Provider(ABC):
    """Base interface for all provider implementations."""

    name: str = "provider"

    def __init__(self, config: ProviderConfig | None = None) -> None:
        self.config = config or ProviderConfig(name=self.name)
        self.config.validate()
        self.state = ProviderState(name=self.config.name or self.name)
        self.metrics = ProviderMetrics()
        self._capabilities: list[ProviderCapability] = []
        # policy helpers
        self._retry_policy = RetryPolicy(retries=self.config.retries)
        self._timeout_policy = TimeoutPolicy(timeout_seconds=float(self.config.timeout))
        self._circuit_breaker = CircuitBreaker()

    @property
    def capabilities(self) -> list[ProviderCapability]:
        """Return the provider capabilities."""
        return list(self._capabilities)

    def register_capability(self, capability: ProviderCapability) -> None:
        """Register a capability exposed by the provider."""
        self._capabilities.append(capability)

    def set_state(self, status: ProviderStatus | str, error: str | None = None) -> None:
        """Update provider runtime state."""
        self.state.set_status(status, error)

    def is_ready(self) -> bool:
        """Return whether the provider is ready for operations."""
        return self.state.status == ProviderStatus.READY

    @abstractmethod
    def initialize(self) -> None:
        """Initialize the provider."""

    @abstractmethod
    def shutdown(self) -> None:
        """Shutdown the provider."""

    @abstractmethod
    def health_check(self) -> ProviderHealth:
        """Return the current provider health."""

    def get_metrics(self) -> ProviderMetrics:
        """Return runtime metrics for the provider."""
        return self.metrics

    def execute(self, *args: Any, **kwargs: Any) -> Any:
        """Execute a provider operation."""
        # Backwards-compatible behavior: if subclass defines `_run`, call it
        run_fn = getattr(self, "_run", None)
        if callable(run_fn):
            return self.protected_call(run_fn, *args, **kwargs)

        raise NotImplementedError(f"{self.__class__.__name__} does not implement execution")

    def authenticate(self) -> dict[str, str]:
        """Return headers/auth details for external calls using `config`."""
        headers: dict[str, str] = {}
        if self.config.api_key:
            headers["Authorization"] = f"Bearer {self.config.api_key}"
        return headers

    def protected_call(self, func: Callable[..., Any], *args: Any, **kwargs: Any) -> Any:
        """Run a function through timeout, circuit breaker and retry policies."""

        def wrapped() -> Any:
            # auth injection for HTTP-like calls: provide headers if missing
            if "headers" in kwargs and not kwargs.get("headers"):
                kwargs["headers"] = self.authenticate()
            return func(*args, **kwargs)

        # First apply circuit breaker (it will call the function)
        try:
            return self._circuit_breaker.call(lambda: self._retry_policy.execute(lambda: self._timeout_policy.execute(wrapped)))
        except Exception:
            # update metrics on failure
            try:
                self.metrics.failures += 1
            except Exception:
                pass
            raise

    def close(self) -> None:
        """Compatibility wrapper around shutdown."""
        self.shutdown()
