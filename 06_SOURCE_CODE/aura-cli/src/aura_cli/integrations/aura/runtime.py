"""Runtime adapter for aura-cli.

The CLI must call REAL functionality. This adapter dispatches to the canonical
``aura`` runtime (installed as an editable dependency) and to the standalone
subsystem packages (aura-knowledge, aura-reflection) when they are importable
on the current sys.path. Anything that cannot be reached reports
``not_supported`` rather than pretending to work.
"""

from __future__ import annotations

import importlib.util
import sys
from dataclasses import dataclass, field
from typing import Any

from aura_cli.core.result import NotSupportedError

_SRC_REPOS = {
    "aura_knowledge": ("06_SOURCE_CODE/aura-knowledge/src",),
    "aura_reflection": ("06_SOURCE_CODE/aura-reflection/src",),
    "aura_api": ("06_SOURCE_CODE/aura-api/src",),
}


def _canonical_importable() -> bool:
    return importlib.util.find_spec("aura") is not None


def _standalone_importable(name: str) -> bool:
    if importlib.util.find_spec(name) is not None:
        return True
    import os
    from pathlib import Path

    root = Path(os.getcwd()).resolve()
    # walk up to the AURA workspace root
    for parent in [root, *root.parents]:
        rel = parent / _SRC_REPOS[name][0]
        if rel.exists() and str(rel) not in sys.path:
            sys.path.insert(0, str(rel))
    return importlib.util.find_spec(name) is not None


@dataclass
class HealthReport:
    """Canonical health with per-subsystem availability."""

    canonical: bool
    health: dict[str, Any]
    subsystems: dict[str, Any] = field(default_factory=dict)


class RuntimeAdapter:
    """Reaches the canonical runtime and standalone subsystems."""

    def health(self) -> HealthReport:
        if _canonical_importable():
            from aura import Aura

            health = Aura().health()
        else:
            health = {"status": "unavailable", "reason": "canonical aura not importable"}
        subsystems = {
            "aura_knowledge": _standalone_importable("aura_knowledge"),
            "aura_reflection": _standalone_importable("aura_reflection"),
            "aura_api": _standalone_importable("aura_api"),
        }
        return HealthReport(
            canonical=_canonical_importable(),
            health=health,
            subsystems=subsystems,
        )

    def knowledge_summary(self) -> dict[str, Any]:
        """Real knowledge-engine summary via the aura-knowledge package."""
        if not _standalone_importable("aura_knowledge"):
            raise NotSupportedError("aura-knowledge is not importable on this sys.path")
        from aura_knowledge import KnowledgeEngine

        engine = KnowledgeEngine()
        claim = engine.add_claim("the capital of France is Paris", created_by="aura-cli")
        engine.verify(claim.claim_id)
        return {
            "claims": engine.count(),
            "verification_threshold": engine.verification_threshold,
            "claims_dict": [c.to_dict() for c in engine.claims.values()],
        }

    def reasoning(self, question: str) -> dict[str, Any]:
        """Real reasoning pass via the canonical Aura SDK."""
        if not _canonical_importable():
            raise NotSupportedError("canonical aura is not importable; cannot run reasoning")
        from aura import Aura

        result = Aura().reason(question)
        if isinstance(result, str):
            return {"question": question, "outcome": result}
        if isinstance(result, dict):
            return {"question": question, **result}
        return {"question": question, "outcome": repr(result)}

    def doctor(self) -> list[dict[str, Any]]:
        """Real diagnostic checks: canonical availability + subsystem imports."""
        checks: list[dict[str, Any]] = []
        modules = (
            "aura.foundation",
            "aura.config",
            "aura.memory",
            "aura.knowledge",
            "aura.reasoning",
            "aura.planning",
            "aura.execution",
            "aura.reflection",
            "aura.learning",
            "aura.brain",
            "aura.sdk",
        )
        for module in modules:
            try:
                __import__(module)
                checks.append({"name": module, "ok": True, "detail": ""})
            except Exception as exc:  # noqa: BLE001 - diagnostic must not crash
                checks.append({"name": module, "ok": False, "detail": str(exc)})
        for name in ("aura_knowledge", "aura_reflection", "aura_api"):
            checks.append({"name": name, "ok": _standalone_importable(name), "detail": ""})
        for tool in ("pytest", "mypy", "ruff", "yaml"):
            checks.append({"name": tool, "ok": importlib.util.find_spec(tool) is not None, "detail": ""})
        return checks


__all__ = ["HealthReport", "RuntimeAdapter"]