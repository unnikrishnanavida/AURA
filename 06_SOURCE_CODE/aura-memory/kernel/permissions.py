"""Production-grade permission evaluation for the AURA memory kernel.

The module implements a small but practical policy engine for subject-action-resource
access checks.  Rules support wildcard matching, priority ordering, context-aware
conditions, and immutable audit metadata so the decision path is deterministic and
observable.
"""

from __future__ import annotations

import importlib.util
import pathlib
import sys
import sysconfig
import threading
import time
from dataclasses import dataclass, field
from enum import Enum
from fnmatch import fnmatchcase
from typing import Any, Dict, List, Mapping, Optional, Sequence


def _load_stdlib_logging_module() -> Any:
    """Load the standard-library logging module even if a local package shadows it."""
    module_name = "_stdlib_logging"
    if module_name in sys.modules:
        return sys.modules[module_name]

    stdlib_root = pathlib.Path(sysconfig.get_paths()["stdlib"])
    module_path = stdlib_root / "logging" / "__init__.py"
    spec = importlib.util.spec_from_file_location(module_name, module_path)
    if spec is None or spec.loader is None:
        raise ImportError("unable to locate the standard library logging module")

    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


logging = _load_stdlib_logging_module()
logger = logging.getLogger(__name__)


class PermissionDecision(str, Enum):
    """Outcome of a permission evaluation."""

    ALLOW = "allow"
    DENY = "deny"


@dataclass(frozen=True, slots=True)
class PermissionRule:
    """A declarative permission rule.

    Attributes:
        name: Stable identifier for the rule.
        effect: Decision emitted when the rule matches.
        subject_pattern: Glob pattern for the subject identity.
        action_pattern: Glob pattern for the action name.
        resource_pattern: Glob pattern for the resource identifier.
        priority: Higher values are evaluated first.
        conditions: Optional context conditions that must all match.
    """

    name: str
    effect: PermissionDecision
    subject_pattern: str = "*"
    action_pattern: str = "*"
    resource_pattern: str = "*"
    priority: int = 0
    conditions: Mapping[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class PermissionAuditEntry:
    """One permission evaluation outcome for observability."""

    subject: str
    action: str
    resource: str
    decision: PermissionDecision
    rule_name: Optional[str]
    matched: bool
    context: Dict[str, Any] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)


class Permissions:
    """Policy engine for kernel permission decisions.

    The engine stores ordered rules, evaluates them against subject/action/resource
    tuples plus optional context, and returns the first applicable rule according
    to priority. Unknown requests default to deny.
    """

    def __init__(self, rules: Optional[Sequence[PermissionRule]] = None) -> None:
        self._rules: List[PermissionRule] = []
        self._lock = threading.RLock()
        self._audit_log: List[PermissionAuditEntry] = []
        self._active = True
        self._started_at = time.time()

        if rules:
            for rule in rules:
                self.register_rule(rule)

    def start(self) -> None:
        """Activate the engine."""
        with self._lock:
            self._active = True
            self._started_at = time.time()

    def shutdown(self) -> None:
        """Deactivate the engine and clear transient state."""
        with self._lock:
            self._active = False

    def register_rule(self, rule: PermissionRule) -> None:
        """Register a rule in priority order."""
        if not rule.name:
            raise ValueError("rule name must be non-empty")
        with self._lock:
            self._rules.append(rule)
            self._rules.sort(key=lambda item: item.priority, reverse=True)

    def remove_rule(self, name: str) -> bool:
        """Remove a rule by name."""
        with self._lock:
            before = len(self._rules)
            self._rules = [rule for rule in self._rules if rule.name != name]
            return len(self._rules) != before

    def evaluate(
        self,
        subject: str,
        action: str,
        resource: str,
        *,
        context: Optional[Mapping[str, Any]] = None,
    ) -> PermissionDecision:
        """Evaluate a request and return the first matching decision.

        Args:
            subject: Identity or role requesting access.
            action: Operation being requested.
            resource: Resource identifier being targeted.
            context: Optional request context used for rule conditions.

        Returns:
            PermissionDecision.ALLOW or PermissionDecision.DENY.
        """
        decision = PermissionDecision.DENY
        matched_rule: Optional[PermissionRule] = None
        normalized_context = dict(context or {})

        with self._lock:
            for rule in self._rules:
                if self._matches(rule, subject, action, resource, normalized_context):
                    matched_rule = rule
                    decision = rule.effect
                    break

            entry = PermissionAuditEntry(
                subject=subject,
                action=action,
                resource=resource,
                decision=decision,
                rule_name=matched_rule.name if matched_rule else None,
                matched=matched_rule is not None,
                context=normalized_context,
            )
            self._audit_log.append(entry)

        return decision

    def health_check(self) -> bool:
        """Return whether the module is healthy."""
        return self._active

    def info(self) -> Dict[str, Any]:
        """Return runtime module metadata."""
        with self._lock:
            return {
                "module": __name__,
                "class": self.__class__.__name__,
                "timestamp": time.time(),
                "active": self._active,
                "rule_count": len(self._rules),
                "audit_entries": len(self._audit_log),
            }

    def describe(self) -> Dict[str, str]:
        """Return a descriptive summary of this module."""
        return {"package": "kernel", "module": "permissions", "engine": "policy"}

    def audit_log(self) -> List[PermissionAuditEntry]:
        """Return a copy of the audit log for external inspection."""
        with self._lock:
            return list(self._audit_log)

    def _matches(
        self,
        rule: PermissionRule,
        subject: str,
        action: str,
        resource: str,
        context: Mapping[str, Any],
    ) -> bool:
        if not fnmatchcase(subject, rule.subject_pattern):
            return False
        if not fnmatchcase(action, rule.action_pattern):
            return False
        if not fnmatchcase(resource, rule.resource_pattern):
            return False
        for key, expected in rule.conditions.items():
            actual = context.get(key)
            if actual != expected:
                return False
        return True


__all__ = ["PermissionAuditEntry", "PermissionDecision", "PermissionRule", "Permissions"]
