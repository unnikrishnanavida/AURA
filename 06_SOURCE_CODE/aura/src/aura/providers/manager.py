"""Canonical provider manager.

The single runtime boundary between reasoning and model providers:

- policy-filtered selection via the ONE :class:`ProviderRegistry`;
- one dispatch path (:meth:`synthesize`) through which the reasoning engine
  consults a generation/synthesis provider with *safe structured context*
  (conclusions + verification only — never hidden chain-of-thought);
- the **one place** where ``provider_failure``-class signals are emitted
  (metrics + audit + usage counters); failures never crash the request — the
  caller falls back to the deterministic path;
- health aggregation and usage introspection for observability.
"""

from __future__ import annotations

import contextlib
import time
from typing import Any

from aura.config.settings import AuraConfig
from aura.providers.base import (
    Provider,
    ProviderPolicy,
    ProviderProfile,
    ProviderRegistry,
    ProviderUsage,
)
from aura.providers.errors import ProviderError, ProviderTimeoutError


def build_provider_manager(cfg: AuraConfig, *, metrics: Any = None, audit: Any = None) -> Any:
    """Build a :class:`ProviderManager` from validated configuration.

    When ``cfg.provider`` is not enabled this returns ``None`` (the default
    deterministic path). Remote providers are only constructed from explicit
    configuration; the embedded provider is always registered so registry
    discovery works even without remote credentials.
    """
    provider_cfg = cfg.provider
    if provider_cfg is None or not provider_cfg.enabled:
        return None
    manager = ProviderManager(metrics=metrics, audit=audit)

    from aura.providers.embedded import EmbeddedReasoningProvider

    manager.register(EmbeddedReasoningProvider(seed=cfg.engines.reasoning_seed))

    if provider_cfg.kind in {"openai", "ollama"} and provider_cfg.base_url and provider_cfg.model:
        from aura.providers.remote import HttpChatProviderAdapter

        manager.register(
            HttpChatProviderAdapter(
                name=provider_cfg.name,
                base_url=provider_cfg.base_url,
                model=provider_cfg.model,
                api_key=provider_cfg.api_key.get_secret_value() if provider_cfg.api_key else None,
                timeout_seconds=provider_cfg.timeout_seconds,
                flavor=provider_cfg.kind,
                privacy_approved=provider_cfg.privacy_approved,
            )
        )
        if provider_cfg.name:
            manager.registry.set_default(provider_cfg.name)
    return manager


class ProviderManager:
    """Policy-enforcing, observable dispatch through the provider boundary."""

    def __init__(
        self,
        registry: ProviderRegistry | None = None,
        *,
        metrics: Any = None,
        audit: Any = None,
        policy: ProviderPolicy | None = None,
        timeout_seconds: float = 15.0,
    ) -> None:
        self._registry = registry or ProviderRegistry()
        self._metrics = metrics
        self._audit = audit
        self._policy = policy or ProviderPolicy()
        self._timeout = timeout_seconds
        self._usage = ProviderUsage()
        self.last_provider: str | None = None

    @property
    def registry(self) -> ProviderRegistry:
        return self._registry

    @property
    def usage(self) -> ProviderUsage:
        return self._usage

    def register(self, provider: Provider, profile: ProviderProfile | None = None) -> None:
        self._registry.register_instance(provider, profile)

    # -- selection -----------------------------------------------------------

    def select(self, *, required_capability: str | None = None) -> list[str]:
        """Policy-filtered candidate provider names (empty when none match)."""
        policy = self._policy
        capability = required_capability or policy.required_capability
        try:
            profile = self._registry.select(
                required_capability=capability,
                latency_budget_ms=policy.latency_budget_ms,
                cost_budget=policy.cost_budget,
                require_local=policy.require_local,
                require_privacy_approved=policy.require_privacy_approved,
                prefer=(self._registry.default,) if self._registry.default else (),
            )
            return [profile.name]
        except Exception:  # noqa: BLE001 - no candidate matched the policy
            if self._registry.instances():
                self._usage.policy_rejections += 1
            return []
# -- dispatch --------------------------------------------------------------

    def synthesize(self, *, question: str, conclusions: Any, verification: Any) -> str | None:
        """Ask the selected synthesis provider for a final safe answer.

        Returns ``None`` when no provider matches policy or when the call
        failed (a ``provider_failure`` signal is emitted and usage recorded);
        never raises — the caller falls back to deterministic synthesis.
        """
        names = self.select()
        if not names:
            return None
        name = names[0]
        self.last_provider = name
        provider = self._registry.get_instance(name)

        safe_context = {
            "question": question,
            "conclusions": [c.to_dict() if hasattr(c, "to_dict") else str(c) for c in conclusions],
            "verification": verification,
        }
        try:
            started = time.monotonic()
            result = provider.reason(question, context=safe_context)
            latency_ms = (time.monotonic() - started) * 1000.0
        except ProviderTimeoutError:
            self._usage.timeouts += 1
            self._fail("provider_timeout", name)
            return None
        except ProviderError as exc:
            self._usage.failures += 1
            self._fail("provider_error", name, str(exc))
            return None
        except Exception as exc:  # noqa: BLE001 - boundary must never propagate
            self._usage.failures += 1
            self._fail("provider_unexpected", name, str(exc))
            return None

        self._usage.calls += 1
        self._usage.total_latency_ms += latency_ms
        self._usage.note_provider(name)
        self._metric("provider_latency_ms", amount=latency_ms)
        self._metric("provider_call", amount=1)
        if result is None or str(result).strip() == "":
            return None
        return str(result)

    # -- observability ---------------------------------------------------------

    def health(self) -> dict[str, bool]:
        return {p.name: bool(p.health()) for p in self._registry.instances()}

    def all_healthy(self) -> bool:
        if self._registry.instances():
            return all(p.health() for p in self._registry.instances())
        return True

    def snapshot(self) -> dict[str, Any]:
        return {
            "providers": self._registry.names(),
            "default": self._registry.default,
            "usage": self._usage.snapshot(),
            "health": self.health(),
        }

    # -- internal -----------------------------------------------------------

    def _metric(self, name: str, amount: int | float = 1) -> None:
        increment = getattr(self._metrics, "increment", None)
        if callable(increment):
            with contextlib.suppress(Exception):
                increment(name, amount=amount)

    def _fail(self, kind: str, provider_name: str, detail: str = "") -> None:
        self._metric("provider_failure", amount=1)
        record = getattr(self._audit, "record", None)
        if callable(record):
            with contextlib.suppress(Exception):
                record(
                    action=f"provider.{kind}",
                    actor="system",
                    resource=provider_name,
                    decision="fallback",
                    reason=f"provider failure ({kind}); deterministic fallback used",
                    payload={"detail": detail} if detail else {},
                )


__all__ = ["ProviderManager", "build_provider_manager"]