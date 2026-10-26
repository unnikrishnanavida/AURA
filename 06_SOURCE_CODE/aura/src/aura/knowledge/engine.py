"""Knowledge base engine.

Stores claims, evidence, and sources; verifies claims against evidence;
flags contradictions; and retrieves knowledge ranked by trust. Claims can be
persisted to a durable JSON store (Phase 2A/2C) with owner scoping so a
restarted process recovers the same knowledge without losing provenance,
confidence, freshness or epistemic state.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from aura.foundation.clock import Clock, SystemClock
from aura.foundation.errors import NotFoundError
from aura.foundation.ids import ClaimId, ExecutionId
from aura.knowledge.contradictions import Contradiction, ContradictionDetector
from aura.knowledge.models import Claim, Evidence, Source, VerificationStatus
from aura.knowledge.trust import TrustModel


def _parse_dt(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        from datetime import UTC

        return parsed.replace(tzinfo=UTC)
    return parsed


#: Max claims persisted in one snapshot: bounded so knowledge growth cannot
#: turn the durability write into an unbounded dump.
MAX_PERSISTED_CLAIMS = 10_000

#: Max bytes accepted for a single persisted snapshot: corrupt/oversized rows
#: are skipped at hydrate time instead of crashing startup.
MAX_SNAPSHOT_BYTES = 10_000_000


def _claim_to_dict(claim: Claim) -> dict[str, Any]:
    """Faithful, deterministic serialization of one Claim (no secrets)."""
    return {
        "id": str(claim.id),
        "statement": claim.statement,
        "predicate": list(claim.predicate),
        "status": claim.status.value,
        "confidence": claim.confidence,
        "provenance": {
            "source": claim.provenance.source,
            "creator": claim.provenance.creator,
            "execution_id": (
                str(claim.provenance.execution_id) if claim.provenance.execution_id is not None else None
            ),
            "details": dict(claim.provenance.details),
        },
        "created_at": claim.created_at.isoformat() if claim.created_at is not None else None,
        "contradicts": list(claim.contradicts),
        "evidence": [
            {
                "content": evidence.content,
                "quality": evidence.quality,
                "collected_at": (
                    evidence.collected_at.isoformat() if evidence.collected_at is not None else None
                ),
                "source": {
                    "id": evidence.source.id,
                    "reliability": evidence.source.reliability,
                    "kind": evidence.source.kind,
                    "metadata": dict(evidence.source.metadata),
                },
            }
            for evidence in claim.evidence
        ],
    }


def _claim_from_dict(data: dict[str, Any]) -> Claim:
    """Rebuild a Claim with its full provenance/confidence/freshness preserved.

    Raises ``ValueError``/``KeyError`` on corrupt rows so the hydrator can
    skip exactly that row; never fabricates provenance or epistemic state.
    """
    from aura.memory.models import Provenance

    if not isinstance(data, dict) or "id" not in data:
        raise ValueError("corrupt knowledge row: missing claim id")
    raw_predicate = data.get("predicate", [])
    if not isinstance(raw_predicate, (list, tuple)) or not all(isinstance(p, str) for p in raw_predicate):
        raise ValueError("corrupt knowledge row: predicate must be a list of strings")
    raw_evidence = data.get("evidence", [])
    if not isinstance(raw_evidence, list):
        raise ValueError("corrupt knowledge row: evidence must be a list")
    raw_contradicts = data.get("contradicts", [])
    if not isinstance(raw_contradicts, (list, tuple)) or not all(
        isinstance(c, str) for c in raw_contradicts
    ):
        raise ValueError("corrupt knowledge row: contradicts must be a list of strings")
    provenance_data = data.get("provenance") or {}
    if not isinstance(provenance_data, dict):
        raise ValueError("corrupt knowledge row: provenance must be an object")
    provenance = Provenance(
        source=str(provenance_data.get("source", "unknown")),
        execution_id=(
            ExecutionId.from_str(provenance_data["execution_id"])
            if provenance_data.get("execution_id")
            else None
        ),
        creator=str(provenance_data.get("creator", "aura")),
        details=dict(provenance_data.get("details") or {}),
    )
    evidence: list[Evidence] = []
    for ev in raw_evidence:
        if not isinstance(ev, dict):
            raise ValueError("corrupt knowledge row: evidence entry must be an object")
        src = ev.get("source") or {}
        if not isinstance(src, dict):
            raise ValueError("corrupt knowledge row: evidence source must be an object")
        metadata = src.get("metadata") or {}
        if not isinstance(metadata, dict):
            raise ValueError("corrupt knowledge row: source metadata must be an object")
        evidence.append(
            Evidence(
                content=str(ev.get("content", "")),
                source=Source(
                    id=str(src.get("id", "source")),
                    reliability=float(src.get("reliability", 0.5)),
                    kind=str(src.get("kind", "document")),
                    metadata=dict(metadata),
                ),
                quality=float(ev.get("quality", 0.5)),
                collected_at=_parse_dt(ev.get("collected_at")),
            )
        )
    return Claim(
        id=ClaimId.from_str(data["id"]),
        statement=str(data.get("statement", "")),
        predicate=tuple(raw_predicate),
        evidence=evidence,
        status=VerificationStatus(data.get("status", "unverified")),
        confidence=float(data.get("confidence", 0.0)),
        provenance=provenance,
        created_at=_parse_dt(data.get("created_at")),
        contradicts=tuple(raw_contradicts),
    )


def _claim_snapshot_size_bytes(claims: list[dict[str, Any]]) -> int:
    import json

    return len(json.dumps(claims, default=str).encode("utf-8"))


class KnowledgeBase:
    """Knowledge repository with optional durability + owner scoping."""

    def __init__(self, *, state_path: str | None = None, clock: Clock | None = None) -> None:
        self.claims: dict[str, Claim] = {}
        self.trust = TrustModel()
        self.detector = ContradictionDetector()
        self._clock: Clock = clock or SystemClock()
        # claim_id -> owner scope (authoritative for owner isolation)
        self._scopes: dict[str, str] = {}
        self._store = None
        if state_path:
            from aura.foundation.persistent import SQLiteJsonStore

            self._store = SQLiteJsonStore(state_path, table="knowledge")
            self._hydrate()

    # -- durability ----------------------------------------------------------

    def _persist(self) -> None:
        import contextlib

        if self._store is None:
            return
        ordered = sorted(self.claims.values(), key=lambda c: str(c.id))
        if len(ordered) > MAX_PERSISTED_CLAIMS:
            ordered = ordered[:MAX_PERSISTED_CLAIMS]
        claim_dicts = [_claim_to_dict(c) for c in ordered]
        if _claim_snapshot_size_bytes(claim_dicts) > MAX_SNAPSHOT_BYTES:
            # Never dump unbounded state: persist the bounded prefix only so a
            # huge knowledge base cannot break the durability write.
            trimmed: list[dict[str, Any]] = []
            for one in claim_dicts:
                candidate = [*trimmed, one]
                if _claim_snapshot_size_bytes(candidate) > MAX_SNAPSHOT_BYTES:
                    break
                trimmed = candidate
            claim_dicts = trimmed
        snapshot = {
            "schema_version": 1,
            "claims": claim_dicts,
            "scopes": {str(k): str(v) for k, v in self._scopes.items()},
        }
        with contextlib.suppress(Exception):  # persistence must not break knowledge
            self._store.put("v1", snapshot)

    def _hydrate(self) -> None:
        if self._store is None:
            return
        try:
            snap = self._store.get("v1") or {}
        except Exception:  # noqa: BLE001 - a corrupt store must not block startup
            return
        if not isinstance(snap, dict):
            return
        raw_claims = snap.get("claims", [])
        if not isinstance(raw_claims, list):
            raw_claims = []
        for data in raw_claims:
            try:
                claim = _claim_from_dict(data)
            except Exception:  # noqa: BLE001 - a corrupt row must not block startup
                continue
            self.claims[str(claim.id)] = claim
        raw_scopes = snap.get("scopes") or {}
        if isinstance(raw_scopes, dict):
            self._scopes = {str(k): str(v) for k, v in raw_scopes.items()}
        else:
            self._scopes = {}
        for claim in list(self.claims.values()):
            self._flag_contradictions(claim)

    def owner_of(self, claim_id: ClaimId) -> str | None:
        return self._scopes.get(str(claim_id))

    # -- core API ------------------------------------------------------------

    def add(self, claim: Claim, *, owner: str | None = None) -> Claim:
        if claim.created_at is None:
            claim.created_at = self._clock.now()
        self.claims[str(claim.id)] = claim
        if owner is not None:
            self._scopes[str(claim.id)] = owner
        self._flag_contradictions(claim)
        self._persist()
        return claim

    def get(self, claim_id: ClaimId, *, owner: str | None = None) -> Claim:
        if str(claim_id) not in self.claims:
            raise NotFoundError(f"claim not found: {claim_id}")
        if owner is not None and self._scopes.get(str(claim_id)) not in (None, owner):
            # Owner isolation on direct lookup: a private claim is invisible to
            # any other owner (same rule as retrieval; frontend filtering is
            # never the boundary).
            raise NotFoundError(f"claim not found: {claim_id}")
        return self.claims[str(claim_id)]

    def verify(self, claim_id: ClaimId, *, require_evidence: bool = True) -> VerificationStatus:
        claim = self.get(claim_id)
        if not claim.evidence and require_evidence:
            claim.status = VerificationStatus.UNVERIFIED
        else:
            claim.status = VerificationStatus.VERIFIED
        return claim.status

    def retrieve(
        self,
        *,
        predicate: tuple[str, ...] = (),
        statement: str = "",
        limit: int = 10,
        owner: str | None = None,
    ) -> list[tuple[Claim, dict[str, float]]]:
        if limit < 1:
            raise ValueError(f"limit must be >= 1, got {limit}")
        candidates = [
            c
            for cid, c in self.claims.items()
            if owner is None or self._scopes.get(cid) in (None, owner)
        ]
        if predicate:
            candidates = [c for c in candidates if c.predicate == predicate]
        if statement:
            ranked = self._rank_by_statement(candidates, statement, now=self._clock.now())
        else:
            ranked = sorted(
                candidates,
                key=lambda c: self.trust.assess(c, now=self._clock.now())["trust"],
                reverse=True,
            )
        return [(claim, self.trust.assess(claim, now=self._clock.now())) for claim in ranked[:limit]]

    def _rank_by_statement(
        self, candidates: list[Claim], statement: str, *, now: datetime | None = None
    ) -> list[Claim]:
        """Lexical relevance-first ranking with trust/freshness tie-breaking.

        Exact-substring matches win; otherwise claims sharing at least one
        meaningful (non-stopword) token are ranked by topic overlap first and
        by the existing trust assessment second -- so among equally relevant
        claims the fresher, better-evidenced, verified claim ranks first, and
        uncertainty (UNVERIFIED/CONTESTED/REFUTED multipliers) always survives
        retrieval instead of being flattened into a relevance score.
        """
        from aura.memory.retrieval import meaningful_tokens, token_overlap

        moment = now or self._clock.now()
        query_tokens = meaningful_tokens(statement)
        if not query_tokens and not statement.strip():
            return sorted(
                candidates,
                key=lambda c: self.trust.assess(c, now=moment)["trust"],
                reverse=True,
            )
        needle = statement.lower().strip()
        scored: list[tuple[Claim, float, float]] = []
        for claim in candidates:
            haystack = meaningful_tokens(claim.statement)
            if needle and needle in claim.statement.lower():
                overlap = 1.0
            else:
                overlap = token_overlap(query_tokens, haystack) if query_tokens else 0.0
            if overlap <= 0.0:
                continue
            trust = self.trust.assess(claim, now=moment)["trust"]
            scored.append((claim, overlap, trust))
        # Overlap dominates (relevance first); trust breaks ties (freshness,
        # evidence quality and epistemic status second); id order keeps it
        # fully deterministic.
        scored.sort(key=lambda triple: (triple[1], triple[2], str(triple[0].id)), reverse=True)
        return [claim for claim, _, _ in scored]

    def contradictions(self) -> list[Contradiction]:
        return self.detector.detect(self.claims.values())

    def _flag_contradictions(self, claim: Claim) -> None:
        others = [v for k, v in self.claims.items() if v is not claim]
        for conflict in self.detector.detect([claim, *others]):
            other = conflict.second if str(conflict.first.id) == str(claim.id) else conflict.first
            claim.contradicts = tuple({*claim.contradicts, str(other.id)})
            claim.status = VerificationStatus.CONTESTED
            other.status = VerificationStatus.CONTESTED
            other.contradicts = tuple({*other.contradicts, str(claim.id)})

    def count(self) -> int:
        return len(self.claims)

    def health(self) -> dict[str, object]:
        return {"status": "ok", "claims": self.count()}


__all__ = ["KnowledgeBase"]