"""Deterministic LOCAL cloud simulator.

A real, tested implementation of :class:`CloudClient` used for unit/
integration verification. It is **explicitly SIMULATED** — it never touches a
cloud provider and must never be presented as a live deployment. It enforces
the same cost/IAM guards as a production adapter so policy logic is exercised,
and it records every operation for audit.
"""

from __future__ import annotations

import contextlib
import time
from typing import Any

from aura.cloud.base import CloudPolicy, DeploymentTarget


class SimulatedCloudClient:
    """Local, deterministic cloud operations simulator (SIMULATED, not live)."""

    client_kind = "simulated"

    def __init__(self, *, policy: CloudPolicy | None = None, audit: Any | None = None) -> None:
        self._policy = policy or CloudPolicy()
        self._audit = audit
        self._resources: dict[str, dict[str, Any]] = {}
        self._revisions: dict[str, list[str]] = {}
        self._ops: list[dict[str, Any]] = []

    # -- guards ------------------------------------------------------------

    def _guard(self, target: DeploymentTarget, inst_ct: int) -> None:
        if inst_ct > self._policy.max_instances:
            raise ValueError(
                f"instance count {inst_ct} exceeds policy max {self._policy.max_instances} (cost safety)"
            )
        if not target.region:
            raise ValueError("region is required (targeting a real provider requires an explicit region)")
        if (
            self._policy.require_iam_least_privilege
            and target.region not in {"local"}
            and not getattr(target, "iam_profile", "")
        ):
            # A real adapter would require an IAM least-privilege profile here.
            # The simulator requires an explicit operator flag for non-local
            # regions so least-privilege is a conscious choice, never a default.
            raise ValueError("non-local targets require an explicit iam least-privilege profile")

    def _spend(self, amount: float) -> None:
        self._budget_used = getattr(self, "_budget_used", 0.0) + amount
        if self._budget_used > self._policy.budget_units:
            raise RuntimeError("deployment budget exceeded (cost safety)")

    def _record(self, op: str, target: DeploymentTarget, detail: dict[str, Any]) -> dict[str, Any]:
        self._ops.append({"operation": op, "target": target.environment, **detail})
        record = getattr(self._audit, "record", None)
        if callable(record):
            with contextlib.suppress(Exception):
                record(
                    action=f"cloud.{op}",
                    actor="system",
                    resource=target.environment,
                    decision="allow",
                    reason=f"cloud {op} (simulated)",
                    payload={"region": target.region},
                )
        return detail

    # -- operations ---------------------------------------------------------

    def provision(self, target: DeploymentTarget, *, inst_ct: int = 1) -> dict[str, Any]:
        self._guard(target, inst_ct)
        self._spend(5.0 + 1.5 * inst_ct)
        key = f"{target.environment}:{target.region}"
        self._resources[key] = {"instances": inst_ct, "created": round(time.time(), 3)}
        self._revisions.setdefault(key, []).append("r1")
        return self._record("provision", target, {"instances": inst_ct})

    def health(self, target: DeploymentTarget) -> dict[str, Any]:
        key = f"{target.environment}:{target.region}"
        state = self._resources.get(key)
        if state is None:
            return {"healthy": False, "reason": "not provisioned"}
        return {"healthy": True, "instances": state["instances"]}

    def scale(self, target: DeploymentTarget, inst_ct: int) -> dict[str, Any]:
        self._guard(target, inst_ct)
        self._spend(1.0 * inst_ct)
        key = f"{target.environment}:{target.region}"
        if key not in self._resources:
            raise RuntimeError("cannot scale an unprovisioned target")
        self._resources[key]["instances"] = inst_ct
        return self._record("scale", target, {"instances": inst_ct})

    def deploy(self, target: DeploymentTarget) -> dict[str, Any]:
        key = f"{target.environment}:{target.region}"
        if key not in self._resources:
            raise RuntimeError("cannot deploy to an unprovisioned target")
        revision = f"r{len(self._revisions.setdefault(key, [])) + 1}"
        self._revisions[key].append(revision)
        self._spend(2.0)
        return self._record("deploy", target, {"revision": revision})

    def rollback(self, target: DeploymentTarget, to_revision: str | None = None) -> dict[str, Any]:
        key = f"{target.environment}:{target.region}"
        revisions = self._revisions.get(key, [])
        if not revisions:
            raise RuntimeError("nothing to roll back")
        target_revision = to_revision or (revisions[-2] if len(revisions) > 1 else revisions[0])
        return self._record("rollback", target, {"to_revision": target_revision})

    def op_log(self) -> list[dict[str, Any]]:
        return list(self._ops)


__all__ = ["SimulatedCloudClient"]