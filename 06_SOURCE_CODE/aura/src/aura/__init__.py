"""AURA — Autonomous Universal Reasoning Architecture.

A coherent, integrated intelligence infrastructure:

  * foundation     ids, errors, results, clocks, lifecycle, cancellation
  * config         typed, validated, layered configuration
  * core           bootstrap, DI container, registry, health
  * memory         working / episodic / semantic / procedural memory
  * knowledge      claims, evidence, sources, trust, contradictions
  * reasoning      multi-strategy, uncertainty-first reasoning + consensus
  * research       epistemic ledger, claim passports, reproducibility capsules
  * planning       goal decomposition, risk analysis, plan comparison
  * reflection     post-execution review and improvement signals
  * learning       validated, gated, versioned learning
  * execution      controlled action execution with recovery
  * security       capabilities, permissions, safety, budgets, audit
  * observability  flight recorder, provenance, replay, metrics, logs
  * providers      provider-independent model profiles + embedded provider
  * brain          cognitive orchestration of the full lifecycle
  * sdk            public integration surface (``from aura import Aura``)
  * api            dependency-light HTTP service
  * cli            developer / admin commands

The high-level entry point is :class:`aura.sdk.client.Aura`.
"""

from __future__ import annotations

from aura._version import SCHEMA_VERSION, VERSION, __version__
from aura.sdk.client import Aura

__all__ = ["Aura", "SCHEMA_VERSION", "VERSION", "__version__"]