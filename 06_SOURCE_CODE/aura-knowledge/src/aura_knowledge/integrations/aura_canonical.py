"""Adapter bridging aura-knowledge to the canonical AURA runtime.

The canonical runtime is ``aura/`` (``from aura import Aura``). This module
exposes an *optional* bridge that converts aura-knowledge claims into the
canonical ``aura.knowledge`` types so a downstream canonical engine (e.g. the
canonical ``KnowledgeBase`` or ``TrustModel``) can consume evidence produced
here. It never duplicates the canonical engine; it only translates between
the two explicit contracts.

When the canonical ``aura`` package is not installed, this module degrades
gracefully (functions raise ``ImportError``-derived :class:`BridgeUnavailable`).
"""

from __future__ import annotations

from typing import Any

from aura_knowledge.core.models import Claim, Evidence, Source, VerificationStatus


class BridgeUnavailable(RuntimeError):
    """The canonical aura package is not importable."""


def _canonical() -> Any:
    try:
        from aura.foundation import ids as _ids
        from aura.knowledge import models as _models

        return _ids, _models
    except ImportError as exc:  # pragma: no cover - depends on env
        raise BridgeUnavailable("canonical aura package is not installed") from exc


def to_canonical(claim: Claim) -> Any:
    """Convert an aura-knowledge Claim into a canonical aura Claim.

    The same claim_id is preserved so lineage is traceable across the bridge.
    """
    _ids, _models = _canonical()
    canonical_sources: dict[str, Any] = {}
    for ev in claim.evidence:
        if ev.source.identifier not in canonical_sources:
            canonical_sources[ev.source.identifier] = _models.Source(
                id=ev.source.identifier,
                reliability=ev.source.reputation,
                kind=ev.source.kind,
            )
    evidence = [
        _models.Evidence(
            content=ev.content,
            source=canonical_sources[ev.source.identifier],
            quality=ev.reliability,
            collected_at=ev.captured_at,
        )
        for ev in claim.evidence
    ]
    canonical_status = {
        VerificationStatus.UNVERIFIED: _models.VerificationStatus.UNVERIFIED,
        VerificationStatus.VERIFIED: _models.VerificationStatus.VERIFIED,
        VerificationStatus.REFUTED: _models.VerificationStatus.REFUTED,
        VerificationStatus.CONTESTED: _models.VerificationStatus.CONTESTED,
    }.get(claim.verification, _models.VerificationStatus.UNVERIFIED)
    canonical_claim = _models.Claim(
        id=_ids.ClaimId.from_str(claim.claim_id),
        statement=claim.statement,
        predicate=tuple(claim.predicate),
        evidence=evidence,
        status=canonical_status,
        confidence=claim.confidence.value if claim.confidence else 0.0,
        created_at=claim.created_at,
    )
    return canonical_claim


def from_canonical(canonical_claim: Any) -> Claim:
    """Convert a canonical aura Claim back into an aura-knowledge Claim."""
    _ids, _models = _canonical()
    sources: dict[str, Source] = {}
    evidence: list[Evidence] = []
    for ev in getattr(canonical_claim, "evidence", ()) or ():
        src = getattr(ev, "source", None)
        if src is not None and getattr(src, "id", None) not in sources:
            sources[getattr(src, "id", "unknown")] = Source(
                identifier=getattr(src, "id", "unknown"),
                reputation=getattr(src, "reliability", 0.5),
                kind=getattr(src, "kind", "document"),
            )
        source = sources.get(getattr(src, "id", "unknown"), Source(identifier="unknown"))
        evidence.append(
            Evidence(
                content=getattr(ev, "content", ""),
                support=1.0,  # canonical Evidence does not carry direction
                reliability=getattr(ev, "quality", 0.5),
                source=source,
                captured_at=getattr(ev, "collected_at", None),
            )
        )
    status = getattr(canonical_claim, "status", None)
    verification = {
        _models.VerificationStatus.VERIFIED: VerificationStatus.VERIFIED,
        _models.VerificationStatus.REFUTED: VerificationStatus.REFUTED,
        _models.VerificationStatus.CONTESTED: VerificationStatus.CONTESTED,
    }.get(status, VerificationStatus.UNVERIFIED)
    return Claim(
        statement=getattr(canonical_claim, "statement", ""),
        claim_id=str(canonical_claim.id),
        predicate=tuple(getattr(canonical_claim, "predicate", ()) or ()),
        evidence=evidence,
        verification=verification,
        created_at=getattr(canonical_claim, "created_at", None),
    )


__all__ = ["BridgeUnavailable", "from_canonical", "to_canonical"]