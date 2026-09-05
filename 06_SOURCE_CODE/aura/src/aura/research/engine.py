"""Research engine.

Runs an evidence-aware research cycle for a question:

  decompose -> assess claims -> verify evidence -> classify epistemology
  -> detect contradictions -> synthesize -> issue passports -> capsule
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from aura.foundation.ids import ExecutionId
from aura.research.ledger import ClaimPassport, EpistemicLedger
from aura.research.models import (
    EpistemicStatus,
    Finding,
    ReproducibilityCapsule,
    ResearchInput,
    ResearchQuestion,
    SourceQuality,
)


@dataclass
class ResearchOutput:
    question: ResearchQuestion
    findings: list[Finding] = field(default_factory=list)
    synthesis: str = ""
    overall_confidence: float = 0.0
    epistemic: EpistemicStatus = EpistemicStatus.UNKNOWN
    contradictions: list[tuple[str, str]] = field(default_factory=list)
    novelty_hits: list[str] = field(default_factory=list)
    capsule: ReproducibilityCapsule | None = None
    passports: list[ClaimPassport] = field(default_factory=list)
    execution_id: ExecutionId = field(default_factory=ExecutionId.new)

    def to_dict(self) -> dict[str, Any]:
        return {
            "question": self.question.question,
            "sub_questions": list(self.question.sub_questions),
            "findings": [f.to_dict() for f in self.findings],
            "synthesis": self.synthesis,
            "overall_confidence": self.overall_confidence,
            "epistemic": self.epistemic.value,
            "contradictions": [list(pair) for pair in self.contradictions],
            "novelty_hits": self.novelty_hits,
            "capsule": self.capsule.to_dict() if self.capsule else None,
            "execution_id": str(self.execution_id),
        }


_NEGATIONS = ("does not", "not ", "never", "no ", "cannot")


class ResearchEngine:
    def __init__(self, ledger: EpistemicLedger | None = None, max_claims: int = 100) -> None:
        self.ledger = ledger or EpistemicLedger()
        self.max_claims = max_claims

    def research(self, inp: ResearchInput) -> ResearchOutput:
        question = self._decompose(inp.question)
        findings: list[Finding] = []
        contradictions: list[tuple[str, str]] = []

        for claim in inp.claims[: self.max_claims]:
            finding, contradicting = self._assess(claim, inp)
            findings.append(finding)
            if contradicting:
                contradictions.append((claim, contradicting))
            self.ledger.record(
                claim=claim,
                status=finding.status,
                confidence=finding.confidence,
                evidence_count=finding.evidence_count,
                execution_id=inp.execution_id,
            )
            self.ledger.issue_passport(
                claim=claim,
                origin="research.run",
                execution_id=inp.execution_id,
                supporting=list(finding.supporting),
                contradicting=list(finding.contradicting),
                trust=finding.confidence,
                source_quality=finding.source_quality,
                freshness=finding.source_freshness,
            )

        contradictions = _merge_contradictions(contradictions, self.ledger.contradictions())
        synthesis, overall_conf, epistemic = self._synthesize(findings, contradictions)
        novelty_hits = self._novelty(question.question, inp.claims)

        capsule = ReproducibilityCapsule(
            question=question.question,
            sub_questions=question.sub_questions,
            seed=inp.seed,
            inputs={
                "claims": list(inp.claims),
                "evidence": {k: list(v) for k, v in inp.evidence.items()},
            },
        )

        return ResearchOutput(
            question=question,
            findings=findings,
            synthesis=synthesis,
            overall_confidence=overall_conf,
            epistemic=epistemic,
            contradictions=contradictions,
            novelty_hits=novelty_hits,
            capsule=capsule,
            passports=self.ledger.passports(),
            execution_id=inp.execution_id,
        )

    @staticmethod
    def _decompose(question: ResearchQuestion) -> ResearchQuestion:
        if question.sub_questions:
            return question
        return ResearchQuestion.create(
            question.question,
            sub_questions=(
                f"what evidence exists that supports claim: {question.question}",
                f"what evidence contradicts claim: {question.question}",
            ),
        )

    def _assess(self, claim: str, inp: ResearchInput) -> tuple[Finding, str | None]:
        quality, source_quality, freshness = inp.supports(claim)
        has_evidence = quality > 0.0
        contradicting = self._find_contradicting(claim, inp.claims)

        if has_evidence and quality >= 0.6 and source_quality is SourceQuality.PRIMARY:
            status = EpistemicStatus.EVIDENCE
        elif has_evidence and quality >= 0.5:
            status = EpistemicStatus.INFERENCE
        elif has_evidence:
            status = EpistemicStatus.HYPOTHESIS
        else:
            status = EpistemicStatus.SPECULATION

        evidence_count = 1 if has_evidence else 0
        confidence = round(quality * 0.7 + freshness * 0.2 + (0.1 if evidence_count else 0.0), 6)
        return (
            Finding(
                claim=claim,
                status=status,
                confidence=confidence,
                evidence_count=evidence_count,
                supporting=(claim,) if has_evidence else (),
                contradicting=(contradicting,) if contradicting else (),
                source_quality=source_quality,
                source_freshness=freshness,
            ),
            contradicting,
        )

    @staticmethod
    def _find_contradicting(claim: str, claims: tuple[str, ...]) -> str | None:
        lowered = claim.lower()
        negated = any(lowered.startswith(token) for token in _NEGATIONS) or "not" in lowered
        for other in claims:
            if other == claim:
                continue
            other_lower = other.lower()
            other_negated = any(other_lower.startswith(token) for token in _NEGATIONS) or "not" in other_lower
            if _subject(lowered) == _subject(other_lower) and negated != other_negated:
                return other
        return None

    @staticmethod
    def _synthesize(
        findings: list[Finding], contradictions: list[tuple[str, str]]
    ) -> tuple[str, float, EpistemicStatus]:
        if not findings:
            return "no claims provided; research cannot conclude without evidence", 0.0, EpistemicStatus.UNKNOWN
        if contradictions:
            return "contradictory evidence detected; synthesis requires resolution", 0.0, EpistemicStatus.UNKNOWN
        ranked = sorted(findings, key=lambda f: f.confidence, reverse=True)
        best = ranked[0]
        if best.status is EpistemicStatus.SPECULATION:
            return "no verified evidence supports the claim; classified as speculation", best.confidence, EpistemicStatus.SPECULATION
        summary = "; ".join(f"{f.claim} ({f.status.value}, conf {f.confidence:.2f})" for f in ranked[:3])
        return summary, best.confidence, best.status

    def _novelty(self, question: str, claims: tuple[str, ...]) -> list[str]:
        del claims  # novelty is measured against prior ledger claims
        return [entry.claim for entry in self.ledger.search(question)[:5]]


def _subject(text: str) -> str:
    for token in _NEGATIONS:
        if text.startswith(token):
            text = text[len(token) :].strip()
            break
    return " ".join(text.split()[:2])


def _merge_contradictions(
    direct: list[tuple[str, str]], ledger: list[tuple[str, str]]
) -> list[tuple[str, str]]:
    seen: set[tuple[str, str]] = set()
    merged: list[tuple[str, str]] = []
    for left, right in [*direct, *ledger]:
        pair = (left, right) if left <= right else (right, left)
        if pair not in seen:
            seen.add(pair)
            merged.append(pair)
    return merged


__all__ = ["ResearchEngine", "ResearchOutput"]
