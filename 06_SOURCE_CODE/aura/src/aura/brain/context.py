"""Context assembly: the retrieval half of AURA's context contract.

Turns a user request into one explicit, bounded, attributable
:class:`~aura.reasoning.models.Grounding` built from memory and knowledge --
never from the whole store, never unfiltered, never unattributed.

Design rules enforced here:

- **Relevance, not recency alone.** Memory is scored with the canonical
  :class:`~aura.memory.retrieval.RetrievalScorer`; knowledge is re-ranked by
  token overlap against the question rather than returned wholesale.
- **Budgets are hard.** Item count and total characters are bounded, and
  anything removed is *counted*, so "nothing relevant" stays distinguishable
  from "the budget cut it off".
- **Permissions are enforced.** Memory sensitivity is gated through the existing
  :class:`~aura.memory.policy.MemoryPolicy`; the caller-supplied scope is bound
  to the caller.
- **Provenance survives.** Every item keeps the id, source and scope it came
  from, so an answer can always be traced back to the record.
- **Contradictions are preserved, not resolved.**
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

from aura.input.multimodal import MultimodalObservation, observation_grounding_item
from aura.knowledge.models import VerificationStatus
from aura.memory.models import MemoryType
from aura.memory.policy import MemoryPolicy
from aura.memory.retrieval import RetrievalScorer
from aura.reasoning.models import Grounding, GroundingItem

_TOKEN = re.compile(r"[a-z0-9]+")

#: Ephemeral chat turns are context, not evidence. They are counted for
#: transparency but never promoted to grounding items, because treating the
#: user's own earlier words as stored fact would inflate confidence.
_EXCLUDED_MEMORY_KINDS = frozenset({MemoryType.WORKING})

#: Retrieve more than we keep, so the budget has something to rank and trim.
_CANDIDATE_FACTOR = 3


@dataclass(frozen=True, slots=True)
class ContextBudget:
    """Hard bounds on one assembled context."""

    max_items: int = 8
    max_characters: int = 4000
    max_memory_items: int = 5
    max_knowledge_items: int = 5
    max_candidates: int = 40
    #: Word-boundary overlap a record must reach before it may ground an answer.
    #: This is the real relevance gate: the store's own score mixes in recency,
    #: importance and confidence, which are query-independent, so on their own
    #: they cannot distinguish a relevant record from an unrelated one.
    min_overlap: float = 0.20
    #: ``None`` keeps today's behaviour (owner scope is the only boundary).
    #: An explicit integer engages the sensitivity gate.
    clearance: int | None = None
    min_score: float = 0.0

    def __post_init__(self) -> None:
        for name in ("max_items", "max_characters", "max_memory_items", "max_knowledge_items"):
            if getattr(self, name) < 1:
                raise ValueError(f"{name} must be >= 1, got {getattr(self, name)}")
        if not 0.0 <= self.min_score <= 1.0:
            raise ValueError(f"min_score must be in [0,1], got {self.min_score}")
        if not 0.0 <= self.min_overlap <= 1.0:
            raise ValueError(f"min_overlap must be in [0,1], got {self.min_overlap}")
        if self.clearance is not None and self.clearance < 0:
            raise ValueError(f"clearance must be >= 0 or None, got {self.clearance}")


def _tokens(text: str) -> set[str]:
    return {token for token in _TOKEN.findall(text.casefold()) if len(token) > 2}


def _overlap(query: set[str], text: str) -> float:
    """Fraction of the query's meaningful tokens present in ``text``."""
    if not query:
        return 0.0
    haystack = _tokens(text)
    return len(query & haystack) / len(query)


def _memory_text(entry: Any) -> str:
    """Human-readable text for a memory entry, whatever shape it stores.

    Reads the common content keys written across the codebase (``text``,
    ``content``, ``summary``, ``title``, ``note``, ``question``, ``answer``,
    ``output``, ``detail``) and, if none are present, falls back to joining
    all string values in the payload. This keeps the overlap gate from
    silently excluding entries whose content lives under a different key
    (e.g. note-style memories or replayed episodes).
    """
    content = getattr(entry, "content", None)
    if isinstance(content, dict):
        preferred_keys = (
            "text", "content", "summary", "title",
            "note", "question", "answer", "output", "detail",
        )
        for key in preferred_keys:
            value = content.get(key)
            if isinstance(value, str) and value.strip():
                return value.strip()
        # Fallback: join every string value so no text-bearing entry is
        # invisible to the overlap gate.
        joined = " | ".join(str(v).strip() for v in content.values() if isinstance(v, str) and v.strip())
        if joined:
            return joined
    return str(getattr(entry, "key", "")).strip()
class ContextAssembler:
    """Builds one :class:`Grounding` for a single user request."""

    def __init__(
        self,
        *,
        memory: Any,
        knowledge: Any,
        budget: ContextBudget | None = None,
        scorer: RetrievalScorer | None = None,
        policy: MemoryPolicy | None = None,
    ) -> None:
        self._memory = memory
        self._knowledge = knowledge
        self._budget = budget or ContextBudget()
        self._scorer = scorer or RetrievalScorer()
        self._policy = policy or MemoryPolicy()

    @property
    def budget(self) -> ContextBudget:
        return self._budget

    def assemble(
        self,
        question: str,
        *,
        history: tuple[dict[str, str], ...] = (),
        scope: str | None = None,
        observations: tuple[MultimodalObservation, ...] = (),
    ) -> Grounding:
        """Assemble the bounded context for one request.

        ``observations`` are validated multimodal observations (untrusted,
        ``verified=False``). They are mapped to ``source="observation"`` grounding
        items and ranked alongside memory/knowledge -- attributable in an answer
        but, at their pinned confidence, never promoted to a reasoning premise.
        """
        budget = self._budget
        contradictions = self._contradictions()

        observation_items = [observation_grounding_item(obs) for obs in observations]
        memory_items, filtered = self._memory_items(question, scope=scope)
        candidates: list[GroundingItem] = [
            *observation_items, *memory_items, *self._knowledge_items(question, owner=scope)
        ]

        # Rank once across both sources so the budget is spent on the most
        # relevant evidence regardless of where it came from.
        candidates.sort(key=lambda item: item.belief(), reverse=True)
        kept: list[GroundingItem] = []
        used = 0
        for item in candidates:
            if len(kept) >= budget.max_items or item.score < budget.min_score:
                break
            if used + len(item.text) > budget.max_characters:
                continue
            kept.append(item)
            used += len(item.text)

        dropped = len(candidates) - len(kept)
        return Grounding(
            items=tuple(kept),
            contradictions=contradictions,
            dropped=dropped,
            truncated=dropped > 0,
            filtered=filtered,
            turns=len(history),
        )

    # -- sources ---------------------------------------------------------------

    def _memory_items(self, question: str, *, scope: str | None) -> tuple[list[GroundingItem], int]:
        from aura.memory.engine import MemoryQuery

        budget = self._budget
        query = _tokens(question)
        limit = min(budget.max_candidates, max(budget.max_memory_items, 1) * _CANDIDATE_FACTOR)
        entries = self._memory.recall_any(
            MemoryQuery(text=question, scope=scope, limit=limit),
            terms=tuple(sorted(query)),
        )

        items: list[GroundingItem] = []
        filtered = 0
        for entry in entries:
            if entry.kind in _EXCLUDED_MEMORY_KINDS:
                filtered += 1
                continue
            text = _memory_text(entry)
            if not text:
                filtered += 1
                continue
            overlap = _overlap(query, text)
            if overlap < budget.min_overlap:
                # Relevance gate: an unrelated record must never be able to
                # ground an answer, however recent or important it is.
                filtered += 1
                continue
            if budget.clearance is not None:
                # ``None`` means "no clearance model in force" (today's
                # behaviour: owner scope is the boundary). An explicit
                # clearance engages the default-deny sensitivity gate.
                decision = self._policy.can_access(entry.sensitivity, budget.clearance)
                if not decision.allowed:
                    filtered += 1
                    continue
            # Relevance dominates; the store's own score still contributes
            # importance, confidence and recency as tie-breakers.
            store_score = min(1.0, max(0.0, self._scorer.score(entry, question)))
            score = round(0.6 * overlap + 0.4 * store_score, 6)
            items.append(
                GroundingItem(
                    source="memory",
                    reference=str(entry.id),
                    text=text,
                    score=score,
                    confidence=entry.confidence.combined,
                    # A stored memory entry is an assertion, not a verified
                    # claim: it keeps its own confidence instead of claiming
                    # epistemic verification it never had.
                    verified=False,
                    contradicted=False,
                    scope=entry.scope,
                    provenance={
                        "source": entry.provenance.source,
                        "key": entry.key,
                        "kind": entry.kind.value,
                        "created_at": entry.created_at.isoformat() if entry.created_at else None,
                    },
                )
            )
            if len(items) >= budget.max_memory_items:
                break
        return items, filtered

    def _knowledge_items(self, question: str, *, owner: str | None = None) -> list[GroundingItem]:
        budget = self._budget
        query = _tokens(question)
        try:
            # Owner isolation is enforced at retrieval time, not in the
            # frontend: a scoped request can only surface claims bound to
            # that scope (plus shared/global ones).
            retrieved = self._knowledge.retrieve(
                statement=question, limit=budget.max_candidates, owner=owner
            )
        except Exception:  # noqa: BLE001 - retrieval must never break a request
            return []

        scored: list[GroundingItem] = []
        for claim, trust in retrieved:
            if claim.status is VerificationStatus.REFUTED:
                continue
            overlap = _overlap(query, claim.statement)
            if overlap <= 0.0:
                continue
            trust_value = float(trust.get("trust", 0.0)) if isinstance(trust, dict) else 0.0
            scope = None
            owner_of = getattr(self._knowledge, "owner_of", None)
            if callable(owner_of):
                try:
                    scope = owner_of(claim.id)
                except Exception:  # noqa: BLE001 - provenance detail must never break a request
                    scope = None
            scored.append(
                GroundingItem(
                    source="knowledge",
                    reference=str(claim.id),
                    text=claim.statement,
                    score=round(overlap * (0.5 + 0.5 * trust_value), 6),
                    confidence=trust_value,
                    verified=claim.status is VerificationStatus.VERIFIED,
                    contradicted=bool(claim.contradicts),
                    scope=scope,
                    provenance={
                        "source": claim.provenance.source,
                        "status": claim.status.value,
                        "predicate": list(claim.predicate),
                        "evidence": len(claim.evidence),
                    },
                )
            )
        scored.sort(key=lambda item: item.belief(), reverse=True)
        return scored[: budget.max_knowledge_items]

    def _contradictions(self) -> tuple[tuple[str, str], ...]:
        try:
            found = self._knowledge.contradictions()
        except Exception:  # noqa: BLE001 - detection must never break a request
            return ()
        return tuple((str(item.first.id), str(item.second.id)) for item in found)


__all__ = ["ContextAssembler", "ContextBudget"]