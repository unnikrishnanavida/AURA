"""Prompt-injection resilience boundary.

External content (documents, web research, memory, tool outputs, retrieved
knowledge, agent messages) is treated as *untrusted data*, never as
instructions. This module provides the boundary used by tool/API gates:

- :class:`ContentClassifier` inspects text for instruction-like patterns and
  classifies it as TRUSTED or UNTRUSTED_PAYLOAD;
- :func:`contains_instruction_attempt` detects common injection markers
  (``ignore previous instructions``, ``system:``, tool-call look-alikes);
- :meth:`ContentPolicy.check` is the single choke point that tools and
  retrievers call before handling external text: it returns a decision and a
  reason so the refusal is explainable and auditable.

The policy itself never executes the untrusted text; it only classifies.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from enum import StrEnum


class ContentTrust(StrEnum):
    TRUSTED = "trusted"
    UNTRUSTED = "untrusted"


_INSTRUCTION_MARKERS = (
    "ignore previous",
    "ignore all previous",
    "disregard previous",
    "system prompt",
    "system:",
    "you are now",
    "from now on",
    "repeat after me",
    "pretend you",
    "do not follow",
    "jailbreak",
    "override instructions",
    "<tool_call>",
    "function call:",
    "execute: ",
    "run: ",
    "rm -rf",
    "sudo ",
    "eval(",
    "exec(",
)

_PATTERN = re.compile(
    r"(?i)(ignore|disregard|override).{0,40}(instruction|prompt|previous)|"
    r"system\s*[:=].{0,60}|"
    r"(<|\[|`)(tool_call|function|command)(>|\]|`)",
)


@dataclass(frozen=True, slots=True)
class ContentDecision:
    allowed: bool
    trust: ContentTrust
    reason: str

    def to_dict(self) -> dict[str, str]:
        return {"allowed": str(self.allowed), "trust": self.trust.value, "reason": self.reason}


def contains_instruction_attempt(text: str) -> bool:
    """Return True when ``text`` shows a likely instruction-injection marker."""
    lowered = text.lower()
    return bool(_PATTERN.search(text)) or any(marker in lowered for marker in _INSTRUCTION_MARKERS)


class ContentClassifier:
    """Classify external content as trusted vs untrusted instruction payload."""

    def classify(self, text: str) -> ContentTrust:
        if not text or not text.strip():
            return ContentTrust.TRUSTED
        if contains_instruction_attempt(text):
            return ContentTrust.UNTRUSTED
        return ContentTrust.TRUSTED


class ContentPolicy:
    """Choke point: verify external content before a tool/retriever consumes it."""

    def __init__(self, classifier: ContentClassifier | None = None) -> None:
        self._classifier = classifier or ContentClassifier()

    def check(self, text: str, *, source: str = "external") -> ContentDecision:
        trust = self._classifier.classify(text)
        if trust is ContentTrust.UNTRUSTED:
            return ContentDecision(
                allowed=False,
                trust=trust,
                reason=f"content from {source!r} contains instruction-like text; "
                "treated as data, not instructions",
            )
        return ContentDecision(allowed=True, trust=trust, reason=f"{source} content accepted as data")


__all__ = ["ContentClassifier", "ContentDecision", "ContentPolicy", "ContentTrust", "contains_instruction_attempt"]