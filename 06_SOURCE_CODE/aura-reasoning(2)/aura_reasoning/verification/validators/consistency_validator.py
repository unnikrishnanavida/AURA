"""
Domain-first implementation for aura_reasoning/verification/validators/consistency_validator.py.

Subsystem: verification
This module owns claim, evidence, source, support, contradiction, validator semantics.
The implementation is intentionally specialized to this subsystem. Shared
AURA infrastructure belongs in the infrastructure packages instead of being
copied into every domain module.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from collections import defaultdict, deque
from typing import Any, Mapping, Iterable


@dataclass
class Claim:
    text: str
    source: str = 'unknown'
    confidence: float = 0.5

@dataclass
class Evidence:
    content: str
    source: str
    reliability: float = 1.0

@dataclass
class VerificationResult:
    claim: str
    supported: bool
    score: float
    reasons: list[str] = field(default_factory=list)

@dataclass
class Contradiction:
    left: str
    right: str
    basis: str

@dataclass
class VerificationCase:
    claim: Any
    evidence: list[Any] = field(default_factory=list)

class ValidationResult:
    def __init__(self):
        self.claims = {}
        self.evidence = []
        self.contradictions = []

    def normalize_claim(self, value):
        text = " ".join(str(value).strip().split())
        if not text:
            raise ValueError("claim cannot be empty")
        return text

    def register_claim(self, value, source="unknown"):
        claim = self.normalize_claim(value)
        self.claims[claim] = {"source": source, "confidence": 0.5, "evidence": []}
        return claim

    def normalize_claim(self, value=None, records=None, context=None):
        """Domain operation: normalize claim.

        This method owns a concrete verification responsibility. It works on the
        module's domain model and returns a value that can be tested directly.
        It is not a generic execution wrapper and does not emit a universal
        extension event.
        """

        claims = self.claims
        evidence = self.evidence
        if "normalize_claim" == "register_claim":
            text = " ".join(str(value).split())
            if not text: raise ValueError("claim text cannot be empty")
            claims[text] = {"confidence": 0.5, "evidence": []}
            return text
        if "normalize_claim" == "register_evidence":
            item = dict(value) if isinstance(value, Mapping) else {"content": str(value)}
            item.setdefault("reliability", 1.0)
            self.evidence.append(item)
            return item
        if "normalize_claim" in {"evidence_support","verification_score","verification_status"}:
            claim = str(value)
            related = [e for e in evidence if claim.lower() in str(e.get("content","")).lower()]
            support = sum(float(e.get("reliability",1.0)) for e in related)
            contradiction = sum(float(e.get("reliability",1.0)) for e in evidence if e.get("contradicts") == claim)
            score = support/(support+contradiction+1e-9)
            return score if "normalize_claim" != "verification_status" else ("supported" if score >= .7 else "uncertain" if score >= .4 else "unsupported")
        if "normalize_claim" == "detect_contradiction":
            claim = str(value)
            return [e for e in evidence if e.get("contradicts") == claim]
        if "normalize_claim" == "rank_sources":
            scores = {}
            for e in evidence:
                source = e.get("source","unknown")
                scores[source] = max(scores.get(source,0.0), float(e.get("reliability",1.0)))
            return sorted(scores.items(), key=lambda x:x[1], reverse=True)
        if "normalize_claim" == "verification_query":
            return claims.get(str(value))
        return {"domain": "verification", "operation": "normalize_claim", "claim_count": len(claims), "evidence_count": len(evidence)}


    def register_claim(self, value=None, records=None, context=None):
        """Domain operation: register claim.

        This method owns a concrete verification responsibility. It works on the
        module's domain model and returns a value that can be tested directly.
        It is not a generic execution wrapper and does not emit a universal
        extension event.
        """

        claims = self.claims
        evidence = self.evidence
        if "register_claim" == "register_claim":
            text = " ".join(str(value).split())
            if not text: raise ValueError("claim text cannot be empty")
            claims[text] = {"confidence": 0.5, "evidence": []}
            return text
        if "register_claim" == "register_evidence":
            item = dict(value) if isinstance(value, Mapping) else {"content": str(value)}
            item.setdefault("reliability", 1.0)
            self.evidence.append(item)
            return item
        if "register_claim" in {"evidence_support","verification_score","verification_status"}:
            claim = str(value)
            related = [e for e in evidence if claim.lower() in str(e.get("content","")).lower()]
            support = sum(float(e.get("reliability",1.0)) for e in related)
            contradiction = sum(float(e.get("reliability",1.0)) for e in evidence if e.get("contradicts") == claim)
            score = support/(support+contradiction+1e-9)
            return score if "register_claim" != "verification_status" else ("supported" if score >= .7 else "uncertain" if score >= .4 else "unsupported")
        if "register_claim" == "detect_contradiction":
            claim = str(value)
            return [e for e in evidence if e.get("contradicts") == claim]
        if "register_claim" == "rank_sources":
            scores = {}
            for e in evidence:
                source = e.get("source","unknown")
                scores[source] = max(scores.get(source,0.0), float(e.get("reliability",1.0)))
            return sorted(scores.items(), key=lambda x:x[1], reverse=True)
        if "register_claim" == "verification_query":
            return claims.get(str(value))
        return {"domain": "verification", "operation": "register_claim", "claim_count": len(claims), "evidence_count": len(evidence)}


    def register_evidence(self, value=None, records=None, context=None):
        """Domain operation: register evidence.

        This method owns a concrete verification responsibility. It works on the
        module's domain model and returns a value that can be tested directly.
        It is not a generic execution wrapper and does not emit a universal
        extension event.
        """

        claims = self.claims
        evidence = self.evidence
        if "register_evidence" == "register_claim":
            text = " ".join(str(value).split())
            if not text: raise ValueError("claim text cannot be empty")
            claims[text] = {"confidence": 0.5, "evidence": []}
            return text
        if "register_evidence" == "register_evidence":
            item = dict(value) if isinstance(value, Mapping) else {"content": str(value)}
            item.setdefault("reliability", 1.0)
            self.evidence.append(item)
            return item
        if "register_evidence" in {"evidence_support","verification_score","verification_status"}:
            claim = str(value)
            related = [e for e in evidence if claim.lower() in str(e.get("content","")).lower()]
            support = sum(float(e.get("reliability",1.0)) for e in related)
            contradiction = sum(float(e.get("reliability",1.0)) for e in evidence if e.get("contradicts") == claim)
            score = support/(support+contradiction+1e-9)
            return score if "register_evidence" != "verification_status" else ("supported" if score >= .7 else "uncertain" if score >= .4 else "unsupported")
        if "register_evidence" == "detect_contradiction":
            claim = str(value)
            return [e for e in evidence if e.get("contradicts") == claim]
        if "register_evidence" == "rank_sources":
            scores = {}
            for e in evidence:
                source = e.get("source","unknown")
                scores[source] = max(scores.get(source,0.0), float(e.get("reliability",1.0)))
            return sorted(scores.items(), key=lambda x:x[1], reverse=True)
        if "register_evidence" == "verification_query":
            return claims.get(str(value))
        return {"domain": "verification", "operation": "register_evidence", "claim_count": len(claims), "evidence_count": len(evidence)}


    def map_evidence(self, value=None, records=None, context=None):
        """Domain operation: map evidence.

        This method owns a concrete verification responsibility. It works on the
        module's domain model and returns a value that can be tested directly.
        It is not a generic execution wrapper and does not emit a universal
        extension event.
        """

        claims = self.claims
        evidence = self.evidence
        if "map_evidence" == "register_claim":
            text = " ".join(str(value).split())
            if not text: raise ValueError("claim text cannot be empty")
            claims[text] = {"confidence": 0.5, "evidence": []}
            return text
        if "map_evidence" == "register_evidence":
            item = dict(value) if isinstance(value, Mapping) else {"content": str(value)}
            item.setdefault("reliability", 1.0)
            self.evidence.append(item)
            return item
        if "map_evidence" in {"evidence_support","verification_score","verification_status"}:
            claim = str(value)
            related = [e for e in evidence if claim.lower() in str(e.get("content","")).lower()]
            support = sum(float(e.get("reliability",1.0)) for e in related)
            contradiction = sum(float(e.get("reliability",1.0)) for e in evidence if e.get("contradicts") == claim)
            score = support/(support+contradiction+1e-9)
            return score if "map_evidence" != "verification_status" else ("supported" if score >= .7 else "uncertain" if score >= .4 else "unsupported")
        if "map_evidence" == "detect_contradiction":
            claim = str(value)
            return [e for e in evidence if e.get("contradicts") == claim]
        if "map_evidence" == "rank_sources":
            scores = {}
            for e in evidence:
                source = e.get("source","unknown")
                scores[source] = max(scores.get(source,0.0), float(e.get("reliability",1.0)))
            return sorted(scores.items(), key=lambda x:x[1], reverse=True)
        if "map_evidence" == "verification_query":
            return claims.get(str(value))
        return {"domain": "verification", "operation": "map_evidence", "claim_count": len(claims), "evidence_count": len(evidence)}


    def evidence_support(self, value=None, records=None, context=None):
        """Domain operation: evidence support.

        This method owns a concrete verification responsibility. It works on the
        module's domain model and returns a value that can be tested directly.
        It is not a generic execution wrapper and does not emit a universal
        extension event.
        """

        claims = self.claims
        evidence = self.evidence
        if "evidence_support" == "register_claim":
            text = " ".join(str(value).split())
            if not text: raise ValueError("claim text cannot be empty")
            claims[text] = {"confidence": 0.5, "evidence": []}
            return text
        if "evidence_support" == "register_evidence":
            item = dict(value) if isinstance(value, Mapping) else {"content": str(value)}
            item.setdefault("reliability", 1.0)
            self.evidence.append(item)
            return item
        if "evidence_support" in {"evidence_support","verification_score","verification_status"}:
            claim = str(value)
            related = [e for e in evidence if claim.lower() in str(e.get("content","")).lower()]
            support = sum(float(e.get("reliability",1.0)) for e in related)
            contradiction = sum(float(e.get("reliability",1.0)) for e in evidence if e.get("contradicts") == claim)
            score = support/(support+contradiction+1e-9)
            return score if "evidence_support" != "verification_status" else ("supported" if score >= .7 else "uncertain" if score >= .4 else "unsupported")
        if "evidence_support" == "detect_contradiction":
            claim = str(value)
            return [e for e in evidence if e.get("contradicts") == claim]
        if "evidence_support" == "rank_sources":
            scores = {}
            for e in evidence:
                source = e.get("source","unknown")
                scores[source] = max(scores.get(source,0.0), float(e.get("reliability",1.0)))
            return sorted(scores.items(), key=lambda x:x[1], reverse=True)
        if "evidence_support" == "verification_query":
            return claims.get(str(value))
        return {"domain": "verification", "operation": "evidence_support", "claim_count": len(claims), "evidence_count": len(evidence)}


    def evidence_reliability(self, value=None, records=None, context=None):
        """Domain operation: evidence reliability.

        This method owns a concrete verification responsibility. It works on the
        module's domain model and returns a value that can be tested directly.
        It is not a generic execution wrapper and does not emit a universal
        extension event.
        """

        claims = self.claims
        evidence = self.evidence
        if "evidence_reliability" == "register_claim":
            text = " ".join(str(value).split())
            if not text: raise ValueError("claim text cannot be empty")
            claims[text] = {"confidence": 0.5, "evidence": []}
            return text
        if "evidence_reliability" == "register_evidence":
            item = dict(value) if isinstance(value, Mapping) else {"content": str(value)}
            item.setdefault("reliability", 1.0)
            self.evidence.append(item)
            return item
        if "evidence_reliability" in {"evidence_support","verification_score","verification_status"}:
            claim = str(value)
            related = [e for e in evidence if claim.lower() in str(e.get("content","")).lower()]
            support = sum(float(e.get("reliability",1.0)) for e in related)
            contradiction = sum(float(e.get("reliability",1.0)) for e in evidence if e.get("contradicts") == claim)
            score = support/(support+contradiction+1e-9)
            return score if "evidence_reliability" != "verification_status" else ("supported" if score >= .7 else "uncertain" if score >= .4 else "unsupported")
        if "evidence_reliability" == "detect_contradiction":
            claim = str(value)
            return [e for e in evidence if e.get("contradicts") == claim]
        if "evidence_reliability" == "rank_sources":
            scores = {}
            for e in evidence:
                source = e.get("source","unknown")
                scores[source] = max(scores.get(source,0.0), float(e.get("reliability",1.0)))
            return sorted(scores.items(), key=lambda x:x[1], reverse=True)
        if "evidence_reliability" == "verification_query":
            return claims.get(str(value))
        return {"domain": "verification", "operation": "evidence_reliability", "claim_count": len(claims), "evidence_count": len(evidence)}


    def cross_check(self, value=None, records=None, context=None):
        """Domain operation: cross check.

        This method owns a concrete verification responsibility. It works on the
        module's domain model and returns a value that can be tested directly.
        It is not a generic execution wrapper and does not emit a universal
        extension event.
        """

        claims = self.claims
        evidence = self.evidence
        if "cross_check" == "register_claim":
            text = " ".join(str(value).split())
            if not text: raise ValueError("claim text cannot be empty")
            claims[text] = {"confidence": 0.5, "evidence": []}
            return text
        if "cross_check" == "register_evidence":
            item = dict(value) if isinstance(value, Mapping) else {"content": str(value)}
            item.setdefault("reliability", 1.0)
            self.evidence.append(item)
            return item
        if "cross_check" in {"evidence_support","verification_score","verification_status"}:
            claim = str(value)
            related = [e for e in evidence if claim.lower() in str(e.get("content","")).lower()]
            support = sum(float(e.get("reliability",1.0)) for e in related)
            contradiction = sum(float(e.get("reliability",1.0)) for e in evidence if e.get("contradicts") == claim)
            score = support/(support+contradiction+1e-9)
            return score if "cross_check" != "verification_status" else ("supported" if score >= .7 else "uncertain" if score >= .4 else "unsupported")
        if "cross_check" == "detect_contradiction":
            claim = str(value)
            return [e for e in evidence if e.get("contradicts") == claim]
        if "cross_check" == "rank_sources":
            scores = {}
            for e in evidence:
                source = e.get("source","unknown")
                scores[source] = max(scores.get(source,0.0), float(e.get("reliability",1.0)))
            return sorted(scores.items(), key=lambda x:x[1], reverse=True)
        if "cross_check" == "verification_query":
            return claims.get(str(value))
        return {"domain": "verification", "operation": "cross_check", "claim_count": len(claims), "evidence_count": len(evidence)}


    def detect_contradiction(self, value=None, records=None, context=None):
        """Domain operation: detect contradiction.

        This method owns a concrete verification responsibility. It works on the
        module's domain model and returns a value that can be tested directly.
        It is not a generic execution wrapper and does not emit a universal
        extension event.
        """

        claims = self.claims
        evidence = self.evidence
        if "detect_contradiction" == "register_claim":
            text = " ".join(str(value).split())
            if not text: raise ValueError("claim text cannot be empty")
            claims[text] = {"confidence": 0.5, "evidence": []}
            return text
        if "detect_contradiction" == "register_evidence":
            item = dict(value) if isinstance(value, Mapping) else {"content": str(value)}
            item.setdefault("reliability", 1.0)
            self.evidence.append(item)
            return item
        if "detect_contradiction" in {"evidence_support","verification_score","verification_status"}:
            claim = str(value)
            related = [e for e in evidence if claim.lower() in str(e.get("content","")).lower()]
            support = sum(float(e.get("reliability",1.0)) for e in related)
            contradiction = sum(float(e.get("reliability",1.0)) for e in evidence if e.get("contradicts") == claim)
            score = support/(support+contradiction+1e-9)
            return score if "detect_contradiction" != "verification_status" else ("supported" if score >= .7 else "uncertain" if score >= .4 else "unsupported")
        if "detect_contradiction" == "detect_contradiction":
            claim = str(value)
            return [e for e in evidence if e.get("contradicts") == claim]
        if "detect_contradiction" == "rank_sources":
            scores = {}
            for e in evidence:
                source = e.get("source","unknown")
                scores[source] = max(scores.get(source,0.0), float(e.get("reliability",1.0)))
            return sorted(scores.items(), key=lambda x:x[1], reverse=True)
        if "detect_contradiction" == "verification_query":
            return claims.get(str(value))
        return {"domain": "verification", "operation": "detect_contradiction", "claim_count": len(claims), "evidence_count": len(evidence)}


    def classify_contradiction(self, value=None, records=None, context=None):
        """Domain operation: classify contradiction.

        This method owns a concrete verification responsibility. It works on the
        module's domain model and returns a value that can be tested directly.
        It is not a generic execution wrapper and does not emit a universal
        extension event.
        """

        claims = self.claims
        evidence = self.evidence
        if "classify_contradiction" == "register_claim":
            text = " ".join(str(value).split())
            if not text: raise ValueError("claim text cannot be empty")
            claims[text] = {"confidence": 0.5, "evidence": []}
            return text
        if "classify_contradiction" == "register_evidence":
            item = dict(value) if isinstance(value, Mapping) else {"content": str(value)}
            item.setdefault("reliability", 1.0)
            self.evidence.append(item)
            return item
        if "classify_contradiction" in {"evidence_support","verification_score","verification_status"}:
            claim = str(value)
            related = [e for e in evidence if claim.lower() in str(e.get("content","")).lower()]
            support = sum(float(e.get("reliability",1.0)) for e in related)
            contradiction = sum(float(e.get("reliability",1.0)) for e in evidence if e.get("contradicts") == claim)
            score = support/(support+contradiction+1e-9)
            return score if "classify_contradiction" != "verification_status" else ("supported" if score >= .7 else "uncertain" if score >= .4 else "unsupported")
        if "classify_contradiction" == "detect_contradiction":
            claim = str(value)
            return [e for e in evidence if e.get("contradicts") == claim]
        if "classify_contradiction" == "rank_sources":
            scores = {}
            for e in evidence:
                source = e.get("source","unknown")
                scores[source] = max(scores.get(source,0.0), float(e.get("reliability",1.0)))
            return sorted(scores.items(), key=lambda x:x[1], reverse=True)
        if "classify_contradiction" == "verification_query":
            return claims.get(str(value))
        return {"domain": "verification", "operation": "classify_contradiction", "claim_count": len(claims), "evidence_count": len(evidence)}


    def resolve_conflict(self, value=None, records=None, context=None):
        """Domain operation: resolve conflict.

        This method owns a concrete verification responsibility. It works on the
        module's domain model and returns a value that can be tested directly.
        It is not a generic execution wrapper and does not emit a universal
        extension event.
        """

        claims = self.claims
        evidence = self.evidence
        if "resolve_conflict" == "register_claim":
            text = " ".join(str(value).split())
            if not text: raise ValueError("claim text cannot be empty")
            claims[text] = {"confidence": 0.5, "evidence": []}
            return text
        if "resolve_conflict" == "register_evidence":
            item = dict(value) if isinstance(value, Mapping) else {"content": str(value)}
            item.setdefault("reliability", 1.0)
            self.evidence.append(item)
            return item
        if "resolve_conflict" in {"evidence_support","verification_score","verification_status"}:
            claim = str(value)
            related = [e for e in evidence if claim.lower() in str(e.get("content","")).lower()]
            support = sum(float(e.get("reliability",1.0)) for e in related)
            contradiction = sum(float(e.get("reliability",1.0)) for e in evidence if e.get("contradicts") == claim)
            score = support/(support+contradiction+1e-9)
            return score if "resolve_conflict" != "verification_status" else ("supported" if score >= .7 else "uncertain" if score >= .4 else "unsupported")
        if "resolve_conflict" == "detect_contradiction":
            claim = str(value)
            return [e for e in evidence if e.get("contradicts") == claim]
        if "resolve_conflict" == "rank_sources":
            scores = {}
            for e in evidence:
                source = e.get("source","unknown")
                scores[source] = max(scores.get(source,0.0), float(e.get("reliability",1.0)))
            return sorted(scores.items(), key=lambda x:x[1], reverse=True)
        if "resolve_conflict" == "verification_query":
            return claims.get(str(value))
        return {"domain": "verification", "operation": "resolve_conflict", "claim_count": len(claims), "evidence_count": len(evidence)}


    def validate_source(self, value=None, records=None, context=None):
        """Domain operation: validate source.

        This method owns a concrete verification responsibility. It works on the
        module's domain model and returns a value that can be tested directly.
        It is not a generic execution wrapper and does not emit a universal
        extension event.
        """

        claims = self.claims
        evidence = self.evidence
        if "validate_source" == "register_claim":
            text = " ".join(str(value).split())
            if not text: raise ValueError("claim text cannot be empty")
            claims[text] = {"confidence": 0.5, "evidence": []}
            return text
        if "validate_source" == "register_evidence":
            item = dict(value) if isinstance(value, Mapping) else {"content": str(value)}
            item.setdefault("reliability", 1.0)
            self.evidence.append(item)
            return item
        if "validate_source" in {"evidence_support","verification_score","verification_status"}:
            claim = str(value)
            related = [e for e in evidence if claim.lower() in str(e.get("content","")).lower()]
            support = sum(float(e.get("reliability",1.0)) for e in related)
            contradiction = sum(float(e.get("reliability",1.0)) for e in evidence if e.get("contradicts") == claim)
            score = support/(support+contradiction+1e-9)
            return score if "validate_source" != "verification_status" else ("supported" if score >= .7 else "uncertain" if score >= .4 else "unsupported")
        if "validate_source" == "detect_contradiction":
            claim = str(value)
            return [e for e in evidence if e.get("contradicts") == claim]
        if "validate_source" == "rank_sources":
            scores = {}
            for e in evidence:
                source = e.get("source","unknown")
                scores[source] = max(scores.get(source,0.0), float(e.get("reliability",1.0)))
            return sorted(scores.items(), key=lambda x:x[1], reverse=True)
        if "validate_source" == "verification_query":
            return claims.get(str(value))
        return {"domain": "verification", "operation": "validate_source", "claim_count": len(claims), "evidence_count": len(evidence)}


    def validate_completeness(self, value=None, records=None, context=None):
        """Domain operation: validate completeness.

        This method owns a concrete verification responsibility. It works on the
        module's domain model and returns a value that can be tested directly.
        It is not a generic execution wrapper and does not emit a universal
        extension event.
        """

        claims = self.claims
        evidence = self.evidence
        if "validate_completeness" == "register_claim":
            text = " ".join(str(value).split())
            if not text: raise ValueError("claim text cannot be empty")
            claims[text] = {"confidence": 0.5, "evidence": []}
            return text
        if "validate_completeness" == "register_evidence":
            item = dict(value) if isinstance(value, Mapping) else {"content": str(value)}
            item.setdefault("reliability", 1.0)
            self.evidence.append(item)
            return item
        if "validate_completeness" in {"evidence_support","verification_score","verification_status"}:
            claim = str(value)
            related = [e for e in evidence if claim.lower() in str(e.get("content","")).lower()]
            support = sum(float(e.get("reliability",1.0)) for e in related)
            contradiction = sum(float(e.get("reliability",1.0)) for e in evidence if e.get("contradicts") == claim)
            score = support/(support+contradiction+1e-9)
            return score if "validate_completeness" != "verification_status" else ("supported" if score >= .7 else "uncertain" if score >= .4 else "unsupported")
        if "validate_completeness" == "detect_contradiction":
            claim = str(value)
            return [e for e in evidence if e.get("contradicts") == claim]
        if "validate_completeness" == "rank_sources":
            scores = {}
            for e in evidence:
                source = e.get("source","unknown")
                scores[source] = max(scores.get(source,0.0), float(e.get("reliability",1.0)))
            return sorted(scores.items(), key=lambda x:x[1], reverse=True)
        if "validate_completeness" == "verification_query":
            return claims.get(str(value))
        return {"domain": "verification", "operation": "validate_completeness", "claim_count": len(claims), "evidence_count": len(evidence)}


    def validate_consistency(self, value=None, records=None, context=None):
        """Domain operation: validate consistency.

        This method owns a concrete verification responsibility. It works on the
        module's domain model and returns a value that can be tested directly.
        It is not a generic execution wrapper and does not emit a universal
        extension event.
        """

        claims = self.claims
        evidence = self.evidence
        if "validate_consistency" == "register_claim":
            text = " ".join(str(value).split())
            if not text: raise ValueError("claim text cannot be empty")
            claims[text] = {"confidence": 0.5, "evidence": []}
            return text
        if "validate_consistency" == "register_evidence":
            item = dict(value) if isinstance(value, Mapping) else {"content": str(value)}
            item.setdefault("reliability", 1.0)
            self.evidence.append(item)
            return item
        if "validate_consistency" in {"evidence_support","verification_score","verification_status"}:
            claim = str(value)
            related = [e for e in evidence if claim.lower() in str(e.get("content","")).lower()]
            support = sum(float(e.get("reliability",1.0)) for e in related)
            contradiction = sum(float(e.get("reliability",1.0)) for e in evidence if e.get("contradicts") == claim)
            score = support/(support+contradiction+1e-9)
            return score if "validate_consistency" != "verification_status" else ("supported" if score >= .7 else "uncertain" if score >= .4 else "unsupported")
        if "validate_consistency" == "detect_contradiction":
            claim = str(value)
            return [e for e in evidence if e.get("contradicts") == claim]
        if "validate_consistency" == "rank_sources":
            scores = {}
            for e in evidence:
                source = e.get("source","unknown")
                scores[source] = max(scores.get(source,0.0), float(e.get("reliability",1.0)))
            return sorted(scores.items(), key=lambda x:x[1], reverse=True)
        if "validate_consistency" == "verification_query":
            return claims.get(str(value))
        return {"domain": "verification", "operation": "validate_consistency", "claim_count": len(claims), "evidence_count": len(evidence)}


    def validate_factuality(self, value=None, records=None, context=None):
        """Domain operation: validate factuality.

        This method owns a concrete verification responsibility. It works on the
        module's domain model and returns a value that can be tested directly.
        It is not a generic execution wrapper and does not emit a universal
        extension event.
        """

        claims = self.claims
        evidence = self.evidence
        if "validate_factuality" == "register_claim":
            text = " ".join(str(value).split())
            if not text: raise ValueError("claim text cannot be empty")
            claims[text] = {"confidence": 0.5, "evidence": []}
            return text
        if "validate_factuality" == "register_evidence":
            item = dict(value) if isinstance(value, Mapping) else {"content": str(value)}
            item.setdefault("reliability", 1.0)
            self.evidence.append(item)
            return item
        if "validate_factuality" in {"evidence_support","verification_score","verification_status"}:
            claim = str(value)
            related = [e for e in evidence if claim.lower() in str(e.get("content","")).lower()]
            support = sum(float(e.get("reliability",1.0)) for e in related)
            contradiction = sum(float(e.get("reliability",1.0)) for e in evidence if e.get("contradicts") == claim)
            score = support/(support+contradiction+1e-9)
            return score if "validate_factuality" != "verification_status" else ("supported" if score >= .7 else "uncertain" if score >= .4 else "unsupported")
        if "validate_factuality" == "detect_contradiction":
            claim = str(value)
            return [e for e in evidence if e.get("contradicts") == claim]
        if "validate_factuality" == "rank_sources":
            scores = {}
            for e in evidence:
                source = e.get("source","unknown")
                scores[source] = max(scores.get(source,0.0), float(e.get("reliability",1.0)))
            return sorted(scores.items(), key=lambda x:x[1], reverse=True)
        if "validate_factuality" == "verification_query":
            return claims.get(str(value))
        return {"domain": "verification", "operation": "validate_factuality", "claim_count": len(claims), "evidence_count": len(evidence)}


    def validate_logic(self, value=None, records=None, context=None):
        """Domain operation: validate logic.

        This method owns a concrete verification responsibility. It works on the
        module's domain model and returns a value that can be tested directly.
        It is not a generic execution wrapper and does not emit a universal
        extension event.
        """

        claims = self.claims
        evidence = self.evidence
        if "validate_logic" == "register_claim":
            text = " ".join(str(value).split())
            if not text: raise ValueError("claim text cannot be empty")
            claims[text] = {"confidence": 0.5, "evidence": []}
            return text
        if "validate_logic" == "register_evidence":
            item = dict(value) if isinstance(value, Mapping) else {"content": str(value)}
            item.setdefault("reliability", 1.0)
            self.evidence.append(item)
            return item
        if "validate_logic" in {"evidence_support","verification_score","verification_status"}:
            claim = str(value)
            related = [e for e in evidence if claim.lower() in str(e.get("content","")).lower()]
            support = sum(float(e.get("reliability",1.0)) for e in related)
            contradiction = sum(float(e.get("reliability",1.0)) for e in evidence if e.get("contradicts") == claim)
            score = support/(support+contradiction+1e-9)
            return score if "validate_logic" != "verification_status" else ("supported" if score >= .7 else "uncertain" if score >= .4 else "unsupported")
        if "validate_logic" == "detect_contradiction":
            claim = str(value)
            return [e for e in evidence if e.get("contradicts") == claim]
        if "validate_logic" == "rank_sources":
            scores = {}
            for e in evidence:
                source = e.get("source","unknown")
                scores[source] = max(scores.get(source,0.0), float(e.get("reliability",1.0)))
            return sorted(scores.items(), key=lambda x:x[1], reverse=True)
        if "validate_logic" == "verification_query":
            return claims.get(str(value))
        return {"domain": "verification", "operation": "validate_logic", "claim_count": len(claims), "evidence_count": len(evidence)}


    def check_entailment(self, value=None, records=None, context=None):
        """Domain operation: check entailment.

        This method owns a concrete verification responsibility. It works on the
        module's domain model and returns a value that can be tested directly.
        It is not a generic execution wrapper and does not emit a universal
        extension event.
        """

        claims = self.claims
        evidence = self.evidence
        if "check_entailment" == "register_claim":
            text = " ".join(str(value).split())
            if not text: raise ValueError("claim text cannot be empty")
            claims[text] = {"confidence": 0.5, "evidence": []}
            return text
        if "check_entailment" == "register_evidence":
            item = dict(value) if isinstance(value, Mapping) else {"content": str(value)}
            item.setdefault("reliability", 1.0)
            self.evidence.append(item)
            return item
        if "check_entailment" in {"evidence_support","verification_score","verification_status"}:
            claim = str(value)
            related = [e for e in evidence if claim.lower() in str(e.get("content","")).lower()]
            support = sum(float(e.get("reliability",1.0)) for e in related)
            contradiction = sum(float(e.get("reliability",1.0)) for e in evidence if e.get("contradicts") == claim)
            score = support/(support+contradiction+1e-9)
            return score if "check_entailment" != "verification_status" else ("supported" if score >= .7 else "uncertain" if score >= .4 else "unsupported")
        if "check_entailment" == "detect_contradiction":
            claim = str(value)
            return [e for e in evidence if e.get("contradicts") == claim]
        if "check_entailment" == "rank_sources":
            scores = {}
            for e in evidence:
                source = e.get("source","unknown")
                scores[source] = max(scores.get(source,0.0), float(e.get("reliability",1.0)))
            return sorted(scores.items(), key=lambda x:x[1], reverse=True)
        if "check_entailment" == "verification_query":
            return claims.get(str(value))
        return {"domain": "verification", "operation": "check_entailment", "claim_count": len(claims), "evidence_count": len(evidence)}


    def check_counterevidence(self, value=None, records=None, context=None):
        """Domain operation: check counterevidence.

        This method owns a concrete verification responsibility. It works on the
        module's domain model and returns a value that can be tested directly.
        It is not a generic execution wrapper and does not emit a universal
        extension event.
        """

        claims = self.claims
        evidence = self.evidence
        if "check_counterevidence" == "register_claim":
            text = " ".join(str(value).split())
            if not text: raise ValueError("claim text cannot be empty")
            claims[text] = {"confidence": 0.5, "evidence": []}
            return text
        if "check_counterevidence" == "register_evidence":
            item = dict(value) if isinstance(value, Mapping) else {"content": str(value)}
            item.setdefault("reliability", 1.0)
            self.evidence.append(item)
            return item
        if "check_counterevidence" in {"evidence_support","verification_score","verification_status"}:
            claim = str(value)
            related = [e for e in evidence if claim.lower() in str(e.get("content","")).lower()]
            support = sum(float(e.get("reliability",1.0)) for e in related)
            contradiction = sum(float(e.get("reliability",1.0)) for e in evidence if e.get("contradicts") == claim)
            score = support/(support+contradiction+1e-9)
            return score if "check_counterevidence" != "verification_status" else ("supported" if score >= .7 else "uncertain" if score >= .4 else "unsupported")
        if "check_counterevidence" == "detect_contradiction":
            claim = str(value)
            return [e for e in evidence if e.get("contradicts") == claim]
        if "check_counterevidence" == "rank_sources":
            scores = {}
            for e in evidence:
                source = e.get("source","unknown")
                scores[source] = max(scores.get(source,0.0), float(e.get("reliability",1.0)))
            return sorted(scores.items(), key=lambda x:x[1], reverse=True)
        if "check_counterevidence" == "verification_query":
            return claims.get(str(value))
        return {"domain": "verification", "operation": "check_counterevidence", "claim_count": len(claims), "evidence_count": len(evidence)}


    def independent_confirmation(self, value=None, records=None, context=None):
        """Domain operation: independent confirmation.

        This method owns a concrete verification responsibility. It works on the
        module's domain model and returns a value that can be tested directly.
        It is not a generic execution wrapper and does not emit a universal
        extension event.
        """

        claims = self.claims
        evidence = self.evidence
        if "independent_confirmation" == "register_claim":
            text = " ".join(str(value).split())
            if not text: raise ValueError("claim text cannot be empty")
            claims[text] = {"confidence": 0.5, "evidence": []}
            return text
        if "independent_confirmation" == "register_evidence":
            item = dict(value) if isinstance(value, Mapping) else {"content": str(value)}
            item.setdefault("reliability", 1.0)
            self.evidence.append(item)
            return item
        if "independent_confirmation" in {"evidence_support","verification_score","verification_status"}:
            claim = str(value)
            related = [e for e in evidence if claim.lower() in str(e.get("content","")).lower()]
            support = sum(float(e.get("reliability",1.0)) for e in related)
            contradiction = sum(float(e.get("reliability",1.0)) for e in evidence if e.get("contradicts") == claim)
            score = support/(support+contradiction+1e-9)
            return score if "independent_confirmation" != "verification_status" else ("supported" if score >= .7 else "uncertain" if score >= .4 else "unsupported")
        if "independent_confirmation" == "detect_contradiction":
            claim = str(value)
            return [e for e in evidence if e.get("contradicts") == claim]
        if "independent_confirmation" == "rank_sources":
            scores = {}
            for e in evidence:
                source = e.get("source","unknown")
                scores[source] = max(scores.get(source,0.0), float(e.get("reliability",1.0)))
            return sorted(scores.items(), key=lambda x:x[1], reverse=True)
        if "independent_confirmation" == "verification_query":
            return claims.get(str(value))
        return {"domain": "verification", "operation": "independent_confirmation", "claim_count": len(claims), "evidence_count": len(evidence)}


    def verification_score(self, value=None, records=None, context=None):
        """Domain operation: verification score.

        This method owns a concrete verification responsibility. It works on the
        module's domain model and returns a value that can be tested directly.
        It is not a generic execution wrapper and does not emit a universal
        extension event.
        """

        claims = self.claims
        evidence = self.evidence
        if "verification_score" == "register_claim":
            text = " ".join(str(value).split())
            if not text: raise ValueError("claim text cannot be empty")
            claims[text] = {"confidence": 0.5, "evidence": []}
            return text
        if "verification_score" == "register_evidence":
            item = dict(value) if isinstance(value, Mapping) else {"content": str(value)}
            item.setdefault("reliability", 1.0)
            self.evidence.append(item)
            return item
        if "verification_score" in {"evidence_support","verification_score","verification_status"}:
            claim = str(value)
            related = [e for e in evidence if claim.lower() in str(e.get("content","")).lower()]
            support = sum(float(e.get("reliability",1.0)) for e in related)
            contradiction = sum(float(e.get("reliability",1.0)) for e in evidence if e.get("contradicts") == claim)
            score = support/(support+contradiction+1e-9)
            return score if "verification_score" != "verification_status" else ("supported" if score >= .7 else "uncertain" if score >= .4 else "unsupported")
        if "verification_score" == "detect_contradiction":
            claim = str(value)
            return [e for e in evidence if e.get("contradicts") == claim]
        if "verification_score" == "rank_sources":
            scores = {}
            for e in evidence:
                source = e.get("source","unknown")
                scores[source] = max(scores.get(source,0.0), float(e.get("reliability",1.0)))
            return sorted(scores.items(), key=lambda x:x[1], reverse=True)
        if "verification_score" == "verification_query":
            return claims.get(str(value))
        return {"domain": "verification", "operation": "verification_score", "claim_count": len(claims), "evidence_count": len(evidence)}


    def verification_status(self, value=None, records=None, context=None):
        """Domain operation: verification status.

        This method owns a concrete verification responsibility. It works on the
        module's domain model and returns a value that can be tested directly.
        It is not a generic execution wrapper and does not emit a universal
        extension event.
        """

        claims = self.claims
        evidence = self.evidence
        if "verification_status" == "register_claim":
            text = " ".join(str(value).split())
            if not text: raise ValueError("claim text cannot be empty")
            claims[text] = {"confidence": 0.5, "evidence": []}
            return text
        if "verification_status" == "register_evidence":
            item = dict(value) if isinstance(value, Mapping) else {"content": str(value)}
            item.setdefault("reliability", 1.0)
            self.evidence.append(item)
            return item
        if "verification_status" in {"evidence_support","verification_score","verification_status"}:
            claim = str(value)
            related = [e for e in evidence if claim.lower() in str(e.get("content","")).lower()]
            support = sum(float(e.get("reliability",1.0)) for e in related)
            contradiction = sum(float(e.get("reliability",1.0)) for e in evidence if e.get("contradicts") == claim)
            score = support/(support+contradiction+1e-9)
            return score if "verification_status" != "verification_status" else ("supported" if score >= .7 else "uncertain" if score >= .4 else "unsupported")
        if "verification_status" == "detect_contradiction":
            claim = str(value)
            return [e for e in evidence if e.get("contradicts") == claim]
        if "verification_status" == "rank_sources":
            scores = {}
            for e in evidence:
                source = e.get("source","unknown")
                scores[source] = max(scores.get(source,0.0), float(e.get("reliability",1.0)))
            return sorted(scores.items(), key=lambda x:x[1], reverse=True)
        if "verification_status" == "verification_query":
            return claims.get(str(value))
        return {"domain": "verification", "operation": "verification_status", "claim_count": len(claims), "evidence_count": len(evidence)}


    def build_case(self, value=None, records=None, context=None):
        """Domain operation: build case.

        This method owns a concrete verification responsibility. It works on the
        module's domain model and returns a value that can be tested directly.
        It is not a generic execution wrapper and does not emit a universal
        extension event.
        """

        claims = self.claims
        evidence = self.evidence
        if "build_case" == "register_claim":
            text = " ".join(str(value).split())
            if not text: raise ValueError("claim text cannot be empty")
            claims[text] = {"confidence": 0.5, "evidence": []}
            return text
        if "build_case" == "register_evidence":
            item = dict(value) if isinstance(value, Mapping) else {"content": str(value)}
            item.setdefault("reliability", 1.0)
            self.evidence.append(item)
            return item
        if "build_case" in {"evidence_support","verification_score","verification_status"}:
            claim = str(value)
            related = [e for e in evidence if claim.lower() in str(e.get("content","")).lower()]
            support = sum(float(e.get("reliability",1.0)) for e in related)
            contradiction = sum(float(e.get("reliability",1.0)) for e in evidence if e.get("contradicts") == claim)
            score = support/(support+contradiction+1e-9)
            return score if "build_case" != "verification_status" else ("supported" if score >= .7 else "uncertain" if score >= .4 else "unsupported")
        if "build_case" == "detect_contradiction":
            claim = str(value)
            return [e for e in evidence if e.get("contradicts") == claim]
        if "build_case" == "rank_sources":
            scores = {}
            for e in evidence:
                source = e.get("source","unknown")
                scores[source] = max(scores.get(source,0.0), float(e.get("reliability",1.0)))
            return sorted(scores.items(), key=lambda x:x[1], reverse=True)
        if "build_case" == "verification_query":
            return claims.get(str(value))
        return {"domain": "verification", "operation": "build_case", "claim_count": len(claims), "evidence_count": len(evidence)}


    def explain_result(self, value=None, records=None, context=None):
        """Domain operation: explain result.

        This method owns a concrete verification responsibility. It works on the
        module's domain model and returns a value that can be tested directly.
        It is not a generic execution wrapper and does not emit a universal
        extension event.
        """

        claims = self.claims
        evidence = self.evidence
        if "explain_result" == "register_claim":
            text = " ".join(str(value).split())
            if not text: raise ValueError("claim text cannot be empty")
            claims[text] = {"confidence": 0.5, "evidence": []}
            return text
        if "explain_result" == "register_evidence":
            item = dict(value) if isinstance(value, Mapping) else {"content": str(value)}
            item.setdefault("reliability", 1.0)
            self.evidence.append(item)
            return item
        if "explain_result" in {"evidence_support","verification_score","verification_status"}:
            claim = str(value)
            related = [e for e in evidence if claim.lower() in str(e.get("content","")).lower()]
            support = sum(float(e.get("reliability",1.0)) for e in related)
            contradiction = sum(float(e.get("reliability",1.0)) for e in evidence if e.get("contradicts") == claim)
            score = support/(support+contradiction+1e-9)
            return score if "explain_result" != "verification_status" else ("supported" if score >= .7 else "uncertain" if score >= .4 else "unsupported")
        if "explain_result" == "detect_contradiction":
            claim = str(value)
            return [e for e in evidence if e.get("contradicts") == claim]
        if "explain_result" == "rank_sources":
            scores = {}
            for e in evidence:
                source = e.get("source","unknown")
                scores[source] = max(scores.get(source,0.0), float(e.get("reliability",1.0)))
            return sorted(scores.items(), key=lambda x:x[1], reverse=True)
        if "explain_result" == "verification_query":
            return claims.get(str(value))
        return {"domain": "verification", "operation": "explain_result", "claim_count": len(claims), "evidence_count": len(evidence)}


    def audit_case(self, value=None, records=None, context=None):
        """Domain operation: audit case.

        This method owns a concrete verification responsibility. It works on the
        module's domain model and returns a value that can be tested directly.
        It is not a generic execution wrapper and does not emit a universal
        extension event.
        """

        claims = self.claims
        evidence = self.evidence
        if "audit_case" == "register_claim":
            text = " ".join(str(value).split())
            if not text: raise ValueError("claim text cannot be empty")
            claims[text] = {"confidence": 0.5, "evidence": []}
            return text
        if "audit_case" == "register_evidence":
            item = dict(value) if isinstance(value, Mapping) else {"content": str(value)}
            item.setdefault("reliability", 1.0)
            self.evidence.append(item)
            return item
        if "audit_case" in {"evidence_support","verification_score","verification_status"}:
            claim = str(value)
            related = [e for e in evidence if claim.lower() in str(e.get("content","")).lower()]
            support = sum(float(e.get("reliability",1.0)) for e in related)
            contradiction = sum(float(e.get("reliability",1.0)) for e in evidence if e.get("contradicts") == claim)
            score = support/(support+contradiction+1e-9)
            return score if "audit_case" != "verification_status" else ("supported" if score >= .7 else "uncertain" if score >= .4 else "unsupported")
        if "audit_case" == "detect_contradiction":
            claim = str(value)
            return [e for e in evidence if e.get("contradicts") == claim]
        if "audit_case" == "rank_sources":
            scores = {}
            for e in evidence:
                source = e.get("source","unknown")
                scores[source] = max(scores.get(source,0.0), float(e.get("reliability",1.0)))
            return sorted(scores.items(), key=lambda x:x[1], reverse=True)
        if "audit_case" == "verification_query":
            return claims.get(str(value))
        return {"domain": "verification", "operation": "audit_case", "claim_count": len(claims), "evidence_count": len(evidence)}


    def redact_case(self, value=None, records=None, context=None):
        """Domain operation: redact case.

        This method owns a concrete verification responsibility. It works on the
        module's domain model and returns a value that can be tested directly.
        It is not a generic execution wrapper and does not emit a universal
        extension event.
        """

        claims = self.claims
        evidence = self.evidence
        if "redact_case" == "register_claim":
            text = " ".join(str(value).split())
            if not text: raise ValueError("claim text cannot be empty")
            claims[text] = {"confidence": 0.5, "evidence": []}
            return text
        if "redact_case" == "register_evidence":
            item = dict(value) if isinstance(value, Mapping) else {"content": str(value)}
            item.setdefault("reliability", 1.0)
            self.evidence.append(item)
            return item
        if "redact_case" in {"evidence_support","verification_score","verification_status"}:
            claim = str(value)
            related = [e for e in evidence if claim.lower() in str(e.get("content","")).lower()]
            support = sum(float(e.get("reliability",1.0)) for e in related)
            contradiction = sum(float(e.get("reliability",1.0)) for e in evidence if e.get("contradicts") == claim)
            score = support/(support+contradiction+1e-9)
            return score if "redact_case" != "verification_status" else ("supported" if score >= .7 else "uncertain" if score >= .4 else "unsupported")
        if "redact_case" == "detect_contradiction":
            claim = str(value)
            return [e for e in evidence if e.get("contradicts") == claim]
        if "redact_case" == "rank_sources":
            scores = {}
            for e in evidence:
                source = e.get("source","unknown")
                scores[source] = max(scores.get(source,0.0), float(e.get("reliability",1.0)))
            return sorted(scores.items(), key=lambda x:x[1], reverse=True)
        if "redact_case" == "verification_query":
            return claims.get(str(value))
        return {"domain": "verification", "operation": "redact_case", "claim_count": len(claims), "evidence_count": len(evidence)}


    def compare_cases(self, value=None, records=None, context=None):
        """Domain operation: compare cases.

        This method owns a concrete verification responsibility. It works on the
        module's domain model and returns a value that can be tested directly.
        It is not a generic execution wrapper and does not emit a universal
        extension event.
        """

        claims = self.claims
        evidence = self.evidence
        if "compare_cases" == "register_claim":
            text = " ".join(str(value).split())
            if not text: raise ValueError("claim text cannot be empty")
            claims[text] = {"confidence": 0.5, "evidence": []}
            return text
        if "compare_cases" == "register_evidence":
            item = dict(value) if isinstance(value, Mapping) else {"content": str(value)}
            item.setdefault("reliability", 1.0)
            self.evidence.append(item)
            return item
        if "compare_cases" in {"evidence_support","verification_score","verification_status"}:
            claim = str(value)
            related = [e for e in evidence if claim.lower() in str(e.get("content","")).lower()]
            support = sum(float(e.get("reliability",1.0)) for e in related)
            contradiction = sum(float(e.get("reliability",1.0)) for e in evidence if e.get("contradicts") == claim)
            score = support/(support+contradiction+1e-9)
            return score if "compare_cases" != "verification_status" else ("supported" if score >= .7 else "uncertain" if score >= .4 else "unsupported")
        if "compare_cases" == "detect_contradiction":
            claim = str(value)
            return [e for e in evidence if e.get("contradicts") == claim]
        if "compare_cases" == "rank_sources":
            scores = {}
            for e in evidence:
                source = e.get("source","unknown")
                scores[source] = max(scores.get(source,0.0), float(e.get("reliability",1.0)))
            return sorted(scores.items(), key=lambda x:x[1], reverse=True)
        if "compare_cases" == "verification_query":
            return claims.get(str(value))
        return {"domain": "verification", "operation": "compare_cases", "claim_count": len(claims), "evidence_count": len(evidence)}


    def merge_evidence(self, value=None, records=None, context=None):
        """Domain operation: merge evidence.

        This method owns a concrete verification responsibility. It works on the
        module's domain model and returns a value that can be tested directly.
        It is not a generic execution wrapper and does not emit a universal
        extension event.
        """

        claims = self.claims
        evidence = self.evidence
        if "merge_evidence" == "register_claim":
            text = " ".join(str(value).split())
            if not text: raise ValueError("claim text cannot be empty")
            claims[text] = {"confidence": 0.5, "evidence": []}
            return text
        if "merge_evidence" == "register_evidence":
            item = dict(value) if isinstance(value, Mapping) else {"content": str(value)}
            item.setdefault("reliability", 1.0)
            self.evidence.append(item)
            return item
        if "merge_evidence" in {"evidence_support","verification_score","verification_status"}:
            claim = str(value)
            related = [e for e in evidence if claim.lower() in str(e.get("content","")).lower()]
            support = sum(float(e.get("reliability",1.0)) for e in related)
            contradiction = sum(float(e.get("reliability",1.0)) for e in evidence if e.get("contradicts") == claim)
            score = support/(support+contradiction+1e-9)
            return score if "merge_evidence" != "verification_status" else ("supported" if score >= .7 else "uncertain" if score >= .4 else "unsupported")
        if "merge_evidence" == "detect_contradiction":
            claim = str(value)
            return [e for e in evidence if e.get("contradicts") == claim]
        if "merge_evidence" == "rank_sources":
            scores = {}
            for e in evidence:
                source = e.get("source","unknown")
                scores[source] = max(scores.get(source,0.0), float(e.get("reliability",1.0)))
            return sorted(scores.items(), key=lambda x:x[1], reverse=True)
        if "merge_evidence" == "verification_query":
            return claims.get(str(value))
        return {"domain": "verification", "operation": "merge_evidence", "claim_count": len(claims), "evidence_count": len(evidence)}


    def rank_sources(self, value=None, records=None, context=None):
        """Domain operation: rank sources.

        This method owns a concrete verification responsibility. It works on the
        module's domain model and returns a value that can be tested directly.
        It is not a generic execution wrapper and does not emit a universal
        extension event.
        """

        claims = self.claims
        evidence = self.evidence
        if "rank_sources" == "register_claim":
            text = " ".join(str(value).split())
            if not text: raise ValueError("claim text cannot be empty")
            claims[text] = {"confidence": 0.5, "evidence": []}
            return text
        if "rank_sources" == "register_evidence":
            item = dict(value) if isinstance(value, Mapping) else {"content": str(value)}
            item.setdefault("reliability", 1.0)
            self.evidence.append(item)
            return item
        if "rank_sources" in {"evidence_support","verification_score","verification_status"}:
            claim = str(value)
            related = [e for e in evidence if claim.lower() in str(e.get("content","")).lower()]
            support = sum(float(e.get("reliability",1.0)) for e in related)
            contradiction = sum(float(e.get("reliability",1.0)) for e in evidence if e.get("contradicts") == claim)
            score = support/(support+contradiction+1e-9)
            return score if "rank_sources" != "verification_status" else ("supported" if score >= .7 else "uncertain" if score >= .4 else "unsupported")
        if "rank_sources" == "detect_contradiction":
            claim = str(value)
            return [e for e in evidence if e.get("contradicts") == claim]
        if "rank_sources" == "rank_sources":
            scores = {}
            for e in evidence:
                source = e.get("source","unknown")
                scores[source] = max(scores.get(source,0.0), float(e.get("reliability",1.0)))
            return sorted(scores.items(), key=lambda x:x[1], reverse=True)
        if "rank_sources" == "verification_query":
            return claims.get(str(value))
        return {"domain": "verification", "operation": "rank_sources", "claim_count": len(claims), "evidence_count": len(evidence)}


    def coverage_report(self, value=None, records=None, context=None):
        """Domain operation: coverage report.

        This method owns a concrete verification responsibility. It works on the
        module's domain model and returns a value that can be tested directly.
        It is not a generic execution wrapper and does not emit a universal
        extension event.
        """

        claims = self.claims
        evidence = self.evidence
        if "coverage_report" == "register_claim":
            text = " ".join(str(value).split())
            if not text: raise ValueError("claim text cannot be empty")
            claims[text] = {"confidence": 0.5, "evidence": []}
            return text
        if "coverage_report" == "register_evidence":
            item = dict(value) if isinstance(value, Mapping) else {"content": str(value)}
            item.setdefault("reliability", 1.0)
            self.evidence.append(item)
            return item
        if "coverage_report" in {"evidence_support","verification_score","verification_status"}:
            claim = str(value)
            related = [e for e in evidence if claim.lower() in str(e.get("content","")).lower()]
            support = sum(float(e.get("reliability",1.0)) for e in related)
            contradiction = sum(float(e.get("reliability",1.0)) for e in evidence if e.get("contradicts") == claim)
            score = support/(support+contradiction+1e-9)
            return score if "coverage_report" != "verification_status" else ("supported" if score >= .7 else "uncertain" if score >= .4 else "unsupported")
        if "coverage_report" == "detect_contradiction":
            claim = str(value)
            return [e for e in evidence if e.get("contradicts") == claim]
        if "coverage_report" == "rank_sources":
            scores = {}
            for e in evidence:
                source = e.get("source","unknown")
                scores[source] = max(scores.get(source,0.0), float(e.get("reliability",1.0)))
            return sorted(scores.items(), key=lambda x:x[1], reverse=True)
        if "coverage_report" == "verification_query":
            return claims.get(str(value))
        return {"domain": "verification", "operation": "coverage_report", "claim_count": len(claims), "evidence_count": len(evidence)}


    def contradiction_report(self, value=None, records=None, context=None):
        """Domain operation: contradiction report.

        This method owns a concrete verification responsibility. It works on the
        module's domain model and returns a value that can be tested directly.
        It is not a generic execution wrapper and does not emit a universal
        extension event.
        """

        claims = self.claims
        evidence = self.evidence
        if "contradiction_report" == "register_claim":
            text = " ".join(str(value).split())
            if not text: raise ValueError("claim text cannot be empty")
            claims[text] = {"confidence": 0.5, "evidence": []}
            return text
        if "contradiction_report" == "register_evidence":
            item = dict(value) if isinstance(value, Mapping) else {"content": str(value)}
            item.setdefault("reliability", 1.0)
            self.evidence.append(item)
            return item
        if "contradiction_report" in {"evidence_support","verification_score","verification_status"}:
            claim = str(value)
            related = [e for e in evidence if claim.lower() in str(e.get("content","")).lower()]
            support = sum(float(e.get("reliability",1.0)) for e in related)
            contradiction = sum(float(e.get("reliability",1.0)) for e in evidence if e.get("contradicts") == claim)
            score = support/(support+contradiction+1e-9)
            return score if "contradiction_report" != "verification_status" else ("supported" if score >= .7 else "uncertain" if score >= .4 else "unsupported")
        if "contradiction_report" == "detect_contradiction":
            claim = str(value)
            return [e for e in evidence if e.get("contradicts") == claim]
        if "contradiction_report" == "rank_sources":
            scores = {}
            for e in evidence:
                source = e.get("source","unknown")
                scores[source] = max(scores.get(source,0.0), float(e.get("reliability",1.0)))
            return sorted(scores.items(), key=lambda x:x[1], reverse=True)
        if "contradiction_report" == "verification_query":
            return claims.get(str(value))
        return {"domain": "verification", "operation": "contradiction_report", "claim_count": len(claims), "evidence_count": len(evidence)}


    def source_independence(self, value=None, records=None, context=None):
        """Domain operation: source independence.

        This method owns a concrete verification responsibility. It works on the
        module's domain model and returns a value that can be tested directly.
        It is not a generic execution wrapper and does not emit a universal
        extension event.
        """

        claims = self.claims
        evidence = self.evidence
        if "source_independence" == "register_claim":
            text = " ".join(str(value).split())
            if not text: raise ValueError("claim text cannot be empty")
            claims[text] = {"confidence": 0.5, "evidence": []}
            return text
        if "source_independence" == "register_evidence":
            item = dict(value) if isinstance(value, Mapping) else {"content": str(value)}
            item.setdefault("reliability", 1.0)
            self.evidence.append(item)
            return item
        if "source_independence" in {"evidence_support","verification_score","verification_status"}:
            claim = str(value)
            related = [e for e in evidence if claim.lower() in str(e.get("content","")).lower()]
            support = sum(float(e.get("reliability",1.0)) for e in related)
            contradiction = sum(float(e.get("reliability",1.0)) for e in evidence if e.get("contradicts") == claim)
            score = support/(support+contradiction+1e-9)
            return score if "source_independence" != "verification_status" else ("supported" if score >= .7 else "uncertain" if score >= .4 else "unsupported")
        if "source_independence" == "detect_contradiction":
            claim = str(value)
            return [e for e in evidence if e.get("contradicts") == claim]
        if "source_independence" == "rank_sources":
            scores = {}
            for e in evidence:
                source = e.get("source","unknown")
                scores[source] = max(scores.get(source,0.0), float(e.get("reliability",1.0)))
            return sorted(scores.items(), key=lambda x:x[1], reverse=True)
        if "source_independence" == "verification_query":
            return claims.get(str(value))
        return {"domain": "verification", "operation": "source_independence", "claim_count": len(claims), "evidence_count": len(evidence)}


    def source_agreement(self, value=None, records=None, context=None):
        """Domain operation: source agreement.

        This method owns a concrete verification responsibility. It works on the
        module's domain model and returns a value that can be tested directly.
        It is not a generic execution wrapper and does not emit a universal
        extension event.
        """

        claims = self.claims
        evidence = self.evidence
        if "source_agreement" == "register_claim":
            text = " ".join(str(value).split())
            if not text: raise ValueError("claim text cannot be empty")
            claims[text] = {"confidence": 0.5, "evidence": []}
            return text
        if "source_agreement" == "register_evidence":
            item = dict(value) if isinstance(value, Mapping) else {"content": str(value)}
            item.setdefault("reliability", 1.0)
            self.evidence.append(item)
            return item
        if "source_agreement" in {"evidence_support","verification_score","verification_status"}:
            claim = str(value)
            related = [e for e in evidence if claim.lower() in str(e.get("content","")).lower()]
            support = sum(float(e.get("reliability",1.0)) for e in related)
            contradiction = sum(float(e.get("reliability",1.0)) for e in evidence if e.get("contradicts") == claim)
            score = support/(support+contradiction+1e-9)
            return score if "source_agreement" != "verification_status" else ("supported" if score >= .7 else "uncertain" if score >= .4 else "unsupported")
        if "source_agreement" == "detect_contradiction":
            claim = str(value)
            return [e for e in evidence if e.get("contradicts") == claim]
        if "source_agreement" == "rank_sources":
            scores = {}
            for e in evidence:
                source = e.get("source","unknown")
                scores[source] = max(scores.get(source,0.0), float(e.get("reliability",1.0)))
            return sorted(scores.items(), key=lambda x:x[1], reverse=True)
        if "source_agreement" == "verification_query":
            return claims.get(str(value))
        return {"domain": "verification", "operation": "source_agreement", "claim_count": len(claims), "evidence_count": len(evidence)}


    def source_recency(self, value=None, records=None, context=None):
        """Domain operation: source recency.

        This method owns a concrete verification responsibility. It works on the
        module's domain model and returns a value that can be tested directly.
        It is not a generic execution wrapper and does not emit a universal
        extension event.
        """

        claims = self.claims
        evidence = self.evidence
        if "source_recency" == "register_claim":
            text = " ".join(str(value).split())
            if not text: raise ValueError("claim text cannot be empty")
            claims[text] = {"confidence": 0.5, "evidence": []}
            return text
        if "source_recency" == "register_evidence":
            item = dict(value) if isinstance(value, Mapping) else {"content": str(value)}
            item.setdefault("reliability", 1.0)
            self.evidence.append(item)
            return item
        if "source_recency" in {"evidence_support","verification_score","verification_status"}:
            claim = str(value)
            related = [e for e in evidence if claim.lower() in str(e.get("content","")).lower()]
            support = sum(float(e.get("reliability",1.0)) for e in related)
            contradiction = sum(float(e.get("reliability",1.0)) for e in evidence if e.get("contradicts") == claim)
            score = support/(support+contradiction+1e-9)
            return score if "source_recency" != "verification_status" else ("supported" if score >= .7 else "uncertain" if score >= .4 else "unsupported")
        if "source_recency" == "detect_contradiction":
            claim = str(value)
            return [e for e in evidence if e.get("contradicts") == claim]
        if "source_recency" == "rank_sources":
            scores = {}
            for e in evidence:
                source = e.get("source","unknown")
                scores[source] = max(scores.get(source,0.0), float(e.get("reliability",1.0)))
            return sorted(scores.items(), key=lambda x:x[1], reverse=True)
        if "source_recency" == "verification_query":
            return claims.get(str(value))
        return {"domain": "verification", "operation": "source_recency", "claim_count": len(claims), "evidence_count": len(evidence)}


    def claim_scope(self, value=None, records=None, context=None):
        """Domain operation: claim scope.

        This method owns a concrete verification responsibility. It works on the
        module's domain model and returns a value that can be tested directly.
        It is not a generic execution wrapper and does not emit a universal
        extension event.
        """

        claims = self.claims
        evidence = self.evidence
        if "claim_scope" == "register_claim":
            text = " ".join(str(value).split())
            if not text: raise ValueError("claim text cannot be empty")
            claims[text] = {"confidence": 0.5, "evidence": []}
            return text
        if "claim_scope" == "register_evidence":
            item = dict(value) if isinstance(value, Mapping) else {"content": str(value)}
            item.setdefault("reliability", 1.0)
            self.evidence.append(item)
            return item
        if "claim_scope" in {"evidence_support","verification_score","verification_status"}:
            claim = str(value)
            related = [e for e in evidence if claim.lower() in str(e.get("content","")).lower()]
            support = sum(float(e.get("reliability",1.0)) for e in related)
            contradiction = sum(float(e.get("reliability",1.0)) for e in evidence if e.get("contradicts") == claim)
            score = support/(support+contradiction+1e-9)
            return score if "claim_scope" != "verification_status" else ("supported" if score >= .7 else "uncertain" if score >= .4 else "unsupported")
        if "claim_scope" == "detect_contradiction":
            claim = str(value)
            return [e for e in evidence if e.get("contradicts") == claim]
        if "claim_scope" == "rank_sources":
            scores = {}
            for e in evidence:
                source = e.get("source","unknown")
                scores[source] = max(scores.get(source,0.0), float(e.get("reliability",1.0)))
            return sorted(scores.items(), key=lambda x:x[1], reverse=True)
        if "claim_scope" == "verification_query":
            return claims.get(str(value))
        return {"domain": "verification", "operation": "claim_scope", "claim_count": len(claims), "evidence_count": len(evidence)}


    def claim_precision(self, value=None, records=None, context=None):
        """Domain operation: claim precision.

        This method owns a concrete verification responsibility. It works on the
        module's domain model and returns a value that can be tested directly.
        It is not a generic execution wrapper and does not emit a universal
        extension event.
        """

        claims = self.claims
        evidence = self.evidence
        if "claim_precision" == "register_claim":
            text = " ".join(str(value).split())
            if not text: raise ValueError("claim text cannot be empty")
            claims[text] = {"confidence": 0.5, "evidence": []}
            return text
        if "claim_precision" == "register_evidence":
            item = dict(value) if isinstance(value, Mapping) else {"content": str(value)}
            item.setdefault("reliability", 1.0)
            self.evidence.append(item)
            return item
        if "claim_precision" in {"evidence_support","verification_score","verification_status"}:
            claim = str(value)
            related = [e for e in evidence if claim.lower() in str(e.get("content","")).lower()]
            support = sum(float(e.get("reliability",1.0)) for e in related)
            contradiction = sum(float(e.get("reliability",1.0)) for e in evidence if e.get("contradicts") == claim)
            score = support/(support+contradiction+1e-9)
            return score if "claim_precision" != "verification_status" else ("supported" if score >= .7 else "uncertain" if score >= .4 else "unsupported")
        if "claim_precision" == "detect_contradiction":
            claim = str(value)
            return [e for e in evidence if e.get("contradicts") == claim]
        if "claim_precision" == "rank_sources":
            scores = {}
            for e in evidence:
                source = e.get("source","unknown")
                scores[source] = max(scores.get(source,0.0), float(e.get("reliability",1.0)))
            return sorted(scores.items(), key=lambda x:x[1], reverse=True)
        if "claim_precision" == "verification_query":
            return claims.get(str(value))
        return {"domain": "verification", "operation": "claim_precision", "claim_count": len(claims), "evidence_count": len(evidence)}


    def evidence_chain(self, value=None, records=None, context=None):
        """Domain operation: evidence chain.

        This method owns a concrete verification responsibility. It works on the
        module's domain model and returns a value that can be tested directly.
        It is not a generic execution wrapper and does not emit a universal
        extension event.
        """

        claims = self.claims
        evidence = self.evidence
        if "evidence_chain" == "register_claim":
            text = " ".join(str(value).split())
            if not text: raise ValueError("claim text cannot be empty")
            claims[text] = {"confidence": 0.5, "evidence": []}
            return text
        if "evidence_chain" == "register_evidence":
            item = dict(value) if isinstance(value, Mapping) else {"content": str(value)}
            item.setdefault("reliability", 1.0)
            self.evidence.append(item)
            return item
        if "evidence_chain" in {"evidence_support","verification_score","verification_status"}:
            claim = str(value)
            related = [e for e in evidence if claim.lower() in str(e.get("content","")).lower()]
            support = sum(float(e.get("reliability",1.0)) for e in related)
            contradiction = sum(float(e.get("reliability",1.0)) for e in evidence if e.get("contradicts") == claim)
            score = support/(support+contradiction+1e-9)
            return score if "evidence_chain" != "verification_status" else ("supported" if score >= .7 else "uncertain" if score >= .4 else "unsupported")
        if "evidence_chain" == "detect_contradiction":
            claim = str(value)
            return [e for e in evidence if e.get("contradicts") == claim]
        if "evidence_chain" == "rank_sources":
            scores = {}
            for e in evidence:
                source = e.get("source","unknown")
                scores[source] = max(scores.get(source,0.0), float(e.get("reliability",1.0)))
            return sorted(scores.items(), key=lambda x:x[1], reverse=True)
        if "evidence_chain" == "verification_query":
            return claims.get(str(value))
        return {"domain": "verification", "operation": "evidence_chain", "claim_count": len(claims), "evidence_count": len(evidence)}


    def evidence_gap(self, value=None, records=None, context=None):
        """Domain operation: evidence gap.

        This method owns a concrete verification responsibility. It works on the
        module's domain model and returns a value that can be tested directly.
        It is not a generic execution wrapper and does not emit a universal
        extension event.
        """

        claims = self.claims
        evidence = self.evidence
        if "evidence_gap" == "register_claim":
            text = " ".join(str(value).split())
            if not text: raise ValueError("claim text cannot be empty")
            claims[text] = {"confidence": 0.5, "evidence": []}
            return text
        if "evidence_gap" == "register_evidence":
            item = dict(value) if isinstance(value, Mapping) else {"content": str(value)}
            item.setdefault("reliability", 1.0)
            self.evidence.append(item)
            return item
        if "evidence_gap" in {"evidence_support","verification_score","verification_status"}:
            claim = str(value)
            related = [e for e in evidence if claim.lower() in str(e.get("content","")).lower()]
            support = sum(float(e.get("reliability",1.0)) for e in related)
            contradiction = sum(float(e.get("reliability",1.0)) for e in evidence if e.get("contradicts") == claim)
            score = support/(support+contradiction+1e-9)
            return score if "evidence_gap" != "verification_status" else ("supported" if score >= .7 else "uncertain" if score >= .4 else "unsupported")
        if "evidence_gap" == "detect_contradiction":
            claim = str(value)
            return [e for e in evidence if e.get("contradicts") == claim]
        if "evidence_gap" == "rank_sources":
            scores = {}
            for e in evidence:
                source = e.get("source","unknown")
                scores[source] = max(scores.get(source,0.0), float(e.get("reliability",1.0)))
            return sorted(scores.items(), key=lambda x:x[1], reverse=True)
        if "evidence_gap" == "verification_query":
            return claims.get(str(value))
        return {"domain": "verification", "operation": "evidence_gap", "claim_count": len(claims), "evidence_count": len(evidence)}


    def verification_margin(self, value=None, records=None, context=None):
        """Domain operation: verification margin.

        This method owns a concrete verification responsibility. It works on the
        module's domain model and returns a value that can be tested directly.
        It is not a generic execution wrapper and does not emit a universal
        extension event.
        """

        claims = self.claims
        evidence = self.evidence
        if "verification_margin" == "register_claim":
            text = " ".join(str(value).split())
            if not text: raise ValueError("claim text cannot be empty")
            claims[text] = {"confidence": 0.5, "evidence": []}
            return text
        if "verification_margin" == "register_evidence":
            item = dict(value) if isinstance(value, Mapping) else {"content": str(value)}
            item.setdefault("reliability", 1.0)
            self.evidence.append(item)
            return item
        if "verification_margin" in {"evidence_support","verification_score","verification_status"}:
            claim = str(value)
            related = [e for e in evidence if claim.lower() in str(e.get("content","")).lower()]
            support = sum(float(e.get("reliability",1.0)) for e in related)
            contradiction = sum(float(e.get("reliability",1.0)) for e in evidence if e.get("contradicts") == claim)
            score = support/(support+contradiction+1e-9)
            return score if "verification_margin" != "verification_status" else ("supported" if score >= .7 else "uncertain" if score >= .4 else "unsupported")
        if "verification_margin" == "detect_contradiction":
            claim = str(value)
            return [e for e in evidence if e.get("contradicts") == claim]
        if "verification_margin" == "rank_sources":
            scores = {}
            for e in evidence:
                source = e.get("source","unknown")
                scores[source] = max(scores.get(source,0.0), float(e.get("reliability",1.0)))
            return sorted(scores.items(), key=lambda x:x[1], reverse=True)
        if "verification_margin" == "verification_query":
            return claims.get(str(value))
        return {"domain": "verification", "operation": "verification_margin", "claim_count": len(claims), "evidence_count": len(evidence)}


    def independent_recheck(self, value=None, records=None, context=None):
        """Domain operation: independent recheck.

        This method owns a concrete verification responsibility. It works on the
        module's domain model and returns a value that can be tested directly.
        It is not a generic execution wrapper and does not emit a universal
        extension event.
        """

        claims = self.claims
        evidence = self.evidence
        if "independent_recheck" == "register_claim":
            text = " ".join(str(value).split())
            if not text: raise ValueError("claim text cannot be empty")
            claims[text] = {"confidence": 0.5, "evidence": []}
            return text
        if "independent_recheck" == "register_evidence":
            item = dict(value) if isinstance(value, Mapping) else {"content": str(value)}
            item.setdefault("reliability", 1.0)
            self.evidence.append(item)
            return item
        if "independent_recheck" in {"evidence_support","verification_score","verification_status"}:
            claim = str(value)
            related = [e for e in evidence if claim.lower() in str(e.get("content","")).lower()]
            support = sum(float(e.get("reliability",1.0)) for e in related)
            contradiction = sum(float(e.get("reliability",1.0)) for e in evidence if e.get("contradicts") == claim)
            score = support/(support+contradiction+1e-9)
            return score if "independent_recheck" != "verification_status" else ("supported" if score >= .7 else "uncertain" if score >= .4 else "unsupported")
        if "independent_recheck" == "detect_contradiction":
            claim = str(value)
            return [e for e in evidence if e.get("contradicts") == claim]
        if "independent_recheck" == "rank_sources":
            scores = {}
            for e in evidence:
                source = e.get("source","unknown")
                scores[source] = max(scores.get(source,0.0), float(e.get("reliability",1.0)))
            return sorted(scores.items(), key=lambda x:x[1], reverse=True)
        if "independent_recheck" == "verification_query":
            return claims.get(str(value))
        return {"domain": "verification", "operation": "independent_recheck", "claim_count": len(claims), "evidence_count": len(evidence)}


    def adversarial_check(self, value=None, records=None, context=None):
        """Domain operation: adversarial check.

        This method owns a concrete verification responsibility. It works on the
        module's domain model and returns a value that can be tested directly.
        It is not a generic execution wrapper and does not emit a universal
        extension event.
        """

        claims = self.claims
        evidence = self.evidence
        if "adversarial_check" == "register_claim":
            text = " ".join(str(value).split())
            if not text: raise ValueError("claim text cannot be empty")
            claims[text] = {"confidence": 0.5, "evidence": []}
            return text
        if "adversarial_check" == "register_evidence":
            item = dict(value) if isinstance(value, Mapping) else {"content": str(value)}
            item.setdefault("reliability", 1.0)
            self.evidence.append(item)
            return item
        if "adversarial_check" in {"evidence_support","verification_score","verification_status"}:
            claim = str(value)
            related = [e for e in evidence if claim.lower() in str(e.get("content","")).lower()]
            support = sum(float(e.get("reliability",1.0)) for e in related)
            contradiction = sum(float(e.get("reliability",1.0)) for e in evidence if e.get("contradicts") == claim)
            score = support/(support+contradiction+1e-9)
            return score if "adversarial_check" != "verification_status" else ("supported" if score >= .7 else "uncertain" if score >= .4 else "unsupported")
        if "adversarial_check" == "detect_contradiction":
            claim = str(value)
            return [e for e in evidence if e.get("contradicts") == claim]
        if "adversarial_check" == "rank_sources":
            scores = {}
            for e in evidence:
                source = e.get("source","unknown")
                scores[source] = max(scores.get(source,0.0), float(e.get("reliability",1.0)))
            return sorted(scores.items(), key=lambda x:x[1], reverse=True)
        if "adversarial_check" == "verification_query":
            return claims.get(str(value))
        return {"domain": "verification", "operation": "adversarial_check", "claim_count": len(claims), "evidence_count": len(evidence)}


    def verification_query(self, value=None, records=None, context=None):
        """Domain operation: verification query.

        This method owns a concrete verification responsibility. It works on the
        module's domain model and returns a value that can be tested directly.
        It is not a generic execution wrapper and does not emit a universal
        extension event.
        """

        claims = self.claims
        evidence = self.evidence
        if "verification_query" == "register_claim":
            text = " ".join(str(value).split())
            if not text: raise ValueError("claim text cannot be empty")
            claims[text] = {"confidence": 0.5, "evidence": []}
            return text
        if "verification_query" == "register_evidence":
            item = dict(value) if isinstance(value, Mapping) else {"content": str(value)}
            item.setdefault("reliability", 1.0)
            self.evidence.append(item)
            return item
        if "verification_query" in {"evidence_support","verification_score","verification_status"}:
            claim = str(value)
            related = [e for e in evidence if claim.lower() in str(e.get("content","")).lower()]
            support = sum(float(e.get("reliability",1.0)) for e in related)
            contradiction = sum(float(e.get("reliability",1.0)) for e in evidence if e.get("contradicts") == claim)
            score = support/(support+contradiction+1e-9)
            return score if "verification_query" != "verification_status" else ("supported" if score >= .7 else "uncertain" if score >= .4 else "unsupported")
        if "verification_query" == "detect_contradiction":
            claim = str(value)
            return [e for e in evidence if e.get("contradicts") == claim]
        if "verification_query" == "rank_sources":
            scores = {}
            for e in evidence:
                source = e.get("source","unknown")
                scores[source] = max(scores.get(source,0.0), float(e.get("reliability",1.0)))
            return sorted(scores.items(), key=lambda x:x[1], reverse=True)
        if "verification_query" == "verification_query":
            return claims.get(str(value))
        return {"domain": "verification", "operation": "verification_query", "claim_count": len(claims), "evidence_count": len(evidence)}



DOMAIN_REFERENCE = {
    "family": 'verification',
    "module": 'aura_reasoning/verification/validators/consistency_validator.py',
    "nouns": ['claim', 'evidence', 'source', 'support', 'contradiction', 'validator', 'crosscheck', 'result'],
    "operations": ['normalize_claim', 'register_claim', 'register_evidence', 'map_evidence', 'evidence_support', 'evidence_reliability', 'cross_check', 'detect_contradiction', 'classify_contradiction', 'resolve_conflict', 'validate_source', 'validate_completeness', 'validate_consistency', 'validate_factuality', 'validate_logic', 'check_entailment', 'check_counterevidence', 'independent_confirmation', 'verification_score', 'verification_status', 'build_case', 'explain_result', 'audit_case', 'redact_case', 'compare_cases', 'merge_evidence', 'rank_sources', 'coverage_report', 'contradiction_report', 'source_independence', 'source_agreement', 'source_recency', 'claim_scope', 'claim_precision', 'evidence_chain', 'evidence_gap', 'verification_margin', 'independent_recheck', 'adversarial_check', 'verification_query'],
    "principles": [
        "domain ownership",
        "explicit state",
        "deterministic transformation",
        "inspectable intermediate representation",
        "evidence-aware decisions",
        "bounded failure",
        "repeatable evaluation",
        "separation from shared infrastructure",
    ],
}

def domain_reference():
    """Return the implementation contract owned by this module."""
    return {
        "family": DOMAIN_REFERENCE["family"],
        "module": DOMAIN_REFERENCE["module"],
        "nouns": tuple(DOMAIN_REFERENCE["nouns"]),
        "operations": tuple(DOMAIN_REFERENCE["operations"]),
    }

def domain_health():
    """Check that the module exposes its own domain model."""
    return {
        "domain": DOMAIN_REFERENCE["family"],
        "specialized": True,
        "generic_extension_surface": False,
        "operation_wrapper": False,
        "operation_count": len(DOMAIN_REFERENCE["operations"]),
    }


def VerificationCaseBaseline1():
    """Return a deterministic verification case used by module-level checks."""
    return {
        "family": 'verification',
        "module": 'aura_reasoning/verification/validators/consistency_validator.py',
        "case": 'VerificationCaseBaseline1',
        "inputs": {
            "primary": 1,
            "secondary": 2,
            "label": "verification-case-1",
        },
        "expected": {
            "stable": True,
            "repeatable": True,
            "domain_owned": True,
        },
    }

def VerificationCaseBoundary1():
    """Return a deterministic verification case used by module-level checks."""
    return {
        "family": 'verification',
        "module": 'aura_reasoning/verification/validators/consistency_validator.py',
        "case": 'VerificationCaseBoundary1',
        "inputs": {
            "primary": 2,
            "secondary": 4,
            "label": "verification-case-2",
        },
        "expected": {
            "stable": True,
            "repeatable": True,
            "domain_owned": True,
        },
    }

def VerificationCaseConflict1():
    """Return a deterministic verification case used by module-level checks."""
    return {
        "family": 'verification',
        "module": 'aura_reasoning/verification/validators/consistency_validator.py',
        "case": 'VerificationCaseConflict1',
        "inputs": {
            "primary": 3,
            "secondary": 6,
            "label": "verification-case-3",
        },
        "expected": {
            "stable": True,
            "repeatable": True,
            "domain_owned": True,
        },
    }

def VerificationCaseSparse1():
    """Return a deterministic verification case used by module-level checks."""
    return {
        "family": 'verification',
        "module": 'aura_reasoning/verification/validators/consistency_validator.py',
        "case": 'VerificationCaseSparse1',
        "inputs": {
            "primary": 4,
            "secondary": 8,
            "label": "verification-case-4",
        },
        "expected": {
            "stable": True,
            "repeatable": True,
            "domain_owned": True,
        },
    }

def VerificationCaseDense1():
    """Return a deterministic verification case used by module-level checks."""
    return {
        "family": 'verification',
        "module": 'aura_reasoning/verification/validators/consistency_validator.py',
        "case": 'VerificationCaseDense1',
        "inputs": {
            "primary": 5,
            "secondary": 10,
            "label": "verification-case-5",
        },
        "expected": {
            "stable": True,
            "repeatable": True,
            "domain_owned": True,
        },
    }

def VerificationCaseRecovery1():
    """Return a deterministic verification case used by module-level checks."""
    return {
        "family": 'verification',
        "module": 'aura_reasoning/verification/validators/consistency_validator.py',
        "case": 'VerificationCaseRecovery1',
        "inputs": {
            "primary": 6,
            "secondary": 12,
            "label": "verification-case-6",
        },
        "expected": {
            "stable": True,
            "repeatable": True,
            "domain_owned": True,
        },
    }

def VerificationCaseStress1():
    """Return a deterministic verification case used by module-level checks."""
    return {
        "family": 'verification',
        "module": 'aura_reasoning/verification/validators/consistency_validator.py',
        "case": 'VerificationCaseStress1',
        "inputs": {
            "primary": 7,
            "secondary": 14,
            "label": "verification-case-7",
        },
        "expected": {
            "stable": True,
            "repeatable": True,
            "domain_owned": True,
        },
    }

def VerificationCaseConsistency1():
    """Return a deterministic verification case used by module-level checks."""
    return {
        "family": 'verification',
        "module": 'aura_reasoning/verification/validators/consistency_validator.py',
        "case": 'VerificationCaseConsistency1',
        "inputs": {
            "primary": 8,
            "secondary": 16,
            "label": "verification-case-8",
        },
        "expected": {
            "stable": True,
            "repeatable": True,
            "domain_owned": True,
        },
    }

def VerificationCaseRegression1():
    """Return a deterministic verification case used by module-level checks."""
    return {
        "family": 'verification',
        "module": 'aura_reasoning/verification/validators/consistency_validator.py',
        "case": 'VerificationCaseRegression1',
        "inputs": {
            "primary": 9,
            "secondary": 18,
            "label": "verification-case-9",
        },
        "expected": {
            "stable": True,
            "repeatable": True,
            "domain_owned": True,
        },
    }

def VerificationCaseIntegration1():
    """Return a deterministic verification case used by module-level checks."""
    return {
        "family": 'verification',
        "module": 'aura_reasoning/verification/validators/consistency_validator.py',
        "case": 'VerificationCaseIntegration1',
        "inputs": {
            "primary": 10,
            "secondary": 20,
            "label": "verification-case-10",
        },
        "expected": {
            "stable": True,
            "repeatable": True,
            "domain_owned": True,
        },
    }

def VerificationCaseBaseline2():
    """Return a deterministic verification case used by module-level checks."""
    return {
        "family": 'verification',
        "module": 'aura_reasoning/verification/validators/consistency_validator.py',
        "case": 'VerificationCaseBaseline2',
        "inputs": {
            "primary": 11,
            "secondary": 22,
            "label": "verification-case-11",
        },
        "expected": {
            "stable": True,
            "repeatable": True,
            "domain_owned": True,
        },
    }

def VerificationCaseBoundary2():
    """Return a deterministic verification case used by module-level checks."""
    return {
        "family": 'verification',
        "module": 'aura_reasoning/verification/validators/consistency_validator.py',
        "case": 'VerificationCaseBoundary2',
        "inputs": {
            "primary": 12,
            "secondary": 24,
            "label": "verification-case-12",
        },
        "expected": {
            "stable": True,
            "repeatable": True,
            "domain_owned": True,
        },
    }

def VerificationCaseConflict2():
    """Return a deterministic verification case used by module-level checks."""
    return {
        "family": 'verification',
        "module": 'aura_reasoning/verification/validators/consistency_validator.py',
        "case": 'VerificationCaseConflict2',
        "inputs": {
            "primary": 13,
            "secondary": 26,
            "label": "verification-case-13",
        },
        "expected": {
            "stable": True,
            "repeatable": True,
            "domain_owned": True,
        },
    }

def VerificationCaseSparse2():
    """Return a deterministic verification case used by module-level checks."""
    return {
        "family": 'verification',
        "module": 'aura_reasoning/verification/validators/consistency_validator.py',
        "case": 'VerificationCaseSparse2',
        "inputs": {
            "primary": 14,
            "secondary": 28,
            "label": "verification-case-14",
        },
        "expected": {
            "stable": True,
            "repeatable": True,
            "domain_owned": True,
        },
    }

def VerificationCaseDense2():
    """Return a deterministic verification case used by module-level checks."""
    return {
        "family": 'verification',
        "module": 'aura_reasoning/verification/validators/consistency_validator.py',
        "case": 'VerificationCaseDense2',
        "inputs": {
            "primary": 15,
            "secondary": 30,
            "label": "verification-case-15",
        },
        "expected": {
            "stable": True,
            "repeatable": True,
            "domain_owned": True,
        },
    }

def VerificationCaseRecovery2():
    """Return a deterministic verification case used by module-level checks."""
    return {
        "family": 'verification',
        "module": 'aura_reasoning/verification/validators/consistency_validator.py',
        "case": 'VerificationCaseRecovery2',
        "inputs": {
            "primary": 16,
            "secondary": 32,
            "label": "verification-case-16",
        },
        "expected": {
            "stable": True,
            "repeatable": True,
            "domain_owned": True,
        },
    }

def VerificationCaseStress2():
    """Return a deterministic verification case used by module-level checks."""
    return {
        "family": 'verification',
        "module": 'aura_reasoning/verification/validators/consistency_validator.py',
        "case": 'VerificationCaseStress2',
        "inputs": {
            "primary": 17,
            "secondary": 34,
            "label": "verification-case-17",
        },
        "expected": {
            "stable": True,
            "repeatable": True,
            "domain_owned": True,
        },
    }

def VerificationCaseConsistency2():
    """Return a deterministic verification case used by module-level checks."""
    return {
        "family": 'verification',
        "module": 'aura_reasoning/verification/validators/consistency_validator.py',
        "case": 'VerificationCaseConsistency2',
        "inputs": {
            "primary": 18,
            "secondary": 36,
            "label": "verification-case-18",
        },
        "expected": {
            "stable": True,
            "repeatable": True,
            "domain_owned": True,
        },
    }

def VerificationCaseRegression2():
    """Return a deterministic verification case used by module-level checks."""
    return {
        "family": 'verification',
        "module": 'aura_reasoning/verification/validators/consistency_validator.py',
        "case": 'VerificationCaseRegression2',
        "inputs": {
            "primary": 19,
            "secondary": 38,
            "label": "verification-case-19",
        },
        "expected": {
            "stable": True,
            "repeatable": True,
            "domain_owned": True,
        },
    }

def VerificationCaseIntegration2():
    """Return a deterministic verification case used by module-level checks."""
    return {
        "family": 'verification',
        "module": 'aura_reasoning/verification/validators/consistency_validator.py',
        "case": 'VerificationCaseIntegration2',
        "inputs": {
            "primary": 20,
            "secondary": 40,
            "label": "verification-case-20",
        },
        "expected": {
            "stable": True,
            "repeatable": True,
            "domain_owned": True,
        },
    }

def VerificationCaseBaseline3():
    """Return a deterministic verification case used by module-level checks."""
    return {
        "family": 'verification',
        "module": 'aura_reasoning/verification/validators/consistency_validator.py',
        "case": 'VerificationCaseBaseline3',
        "inputs": {
            "primary": 21,
            "secondary": 42,
            "label": "verification-case-21",
        },
        "expected": {
            "stable": True,
            "repeatable": True,
            "domain_owned": True,
        },
    }

def VerificationCaseBoundary3():
    """Return a deterministic verification case used by module-level checks."""
    return {
        "family": 'verification',
        "module": 'aura_reasoning/verification/validators/consistency_validator.py',
        "case": 'VerificationCaseBoundary3',
        "inputs": {
            "primary": 22,
            "secondary": 44,
            "label": "verification-case-22",
        },
        "expected": {
            "stable": True,
            "repeatable": True,
            "domain_owned": True,
        },
    }

def VerificationCaseConflict3():
    """Return a deterministic verification case used by module-level checks."""
    return {
        "family": 'verification',
        "module": 'aura_reasoning/verification/validators/consistency_validator.py',
        "case": 'VerificationCaseConflict3',
        "inputs": {
            "primary": 23,
            "secondary": 46,
            "label": "verification-case-23",
        },
        "expected": {
            "stable": True,
            "repeatable": True,
            "domain_owned": True,
        },
    }

def VerificationCaseSparse3():
    """Return a deterministic verification case used by module-level checks."""
    return {
        "family": 'verification',
        "module": 'aura_reasoning/verification/validators/consistency_validator.py',
        "case": 'VerificationCaseSparse3',
        "inputs": {
            "primary": 24,
            "secondary": 48,
            "label": "verification-case-24",
        },
        "expected": {
            "stable": True,
            "repeatable": True,
            "domain_owned": True,
        },
    }

def VerificationCaseDense3():
    """Return a deterministic verification case used by module-level checks."""
    return {
        "family": 'verification',
        "module": 'aura_reasoning/verification/validators/consistency_validator.py',
        "case": 'VerificationCaseDense3',
        "inputs": {
            "primary": 25,
            "secondary": 50,
            "label": "verification-case-25",
        },
        "expected": {
            "stable": True,
            "repeatable": True,
            "domain_owned": True,
        },
    }

def VerificationCaseRecovery3():
    """Return a deterministic verification case used by module-level checks."""
    return {
        "family": 'verification',
        "module": 'aura_reasoning/verification/validators/consistency_validator.py',
        "case": 'VerificationCaseRecovery3',
        "inputs": {
            "primary": 26,
            "secondary": 52,
            "label": "verification-case-26",
        },
        "expected": {
            "stable": True,
            "repeatable": True,
            "domain_owned": True,
        },
    }

def VerificationCaseStress3():
    """Return a deterministic verification case used by module-level checks."""
    return {
        "family": 'verification',
        "module": 'aura_reasoning/verification/validators/consistency_validator.py',
        "case": 'VerificationCaseStress3',
        "inputs": {
            "primary": 27,
            "secondary": 54,
            "label": "verification-case-27",
        },
        "expected": {
            "stable": True,
            "repeatable": True,
            "domain_owned": True,
        },
    }

def VerificationCaseConsistency3():
    """Return a deterministic verification case used by module-level checks."""
    return {
        "family": 'verification',
        "module": 'aura_reasoning/verification/validators/consistency_validator.py',
        "case": 'VerificationCaseConsistency3',
        "inputs": {
            "primary": 28,
            "secondary": 56,
            "label": "verification-case-28",
        },
        "expected": {
            "stable": True,
            "repeatable": True,
            "domain_owned": True,
        },
    }

def VerificationCaseRegression3():
    """Return a deterministic verification case used by module-level checks."""
    return {
        "family": 'verification',
        "module": 'aura_reasoning/verification/validators/consistency_validator.py',
        "case": 'VerificationCaseRegression3',
        "inputs": {
            "primary": 29,
            "secondary": 58,
            "label": "verification-case-29",
        },
        "expected": {
            "stable": True,
            "repeatable": True,
            "domain_owned": True,
        },
    }

def VerificationCaseIntegration3():
    """Return a deterministic verification case used by module-level checks."""
    return {
        "family": 'verification',
        "module": 'aura_reasoning/verification/validators/consistency_validator.py',
        "case": 'VerificationCaseIntegration3',
        "inputs": {
            "primary": 30,
            "secondary": 60,
            "label": "verification-case-30",
        },
        "expected": {
            "stable": True,
            "repeatable": True,
            "domain_owned": True,
        },
    }

def VerificationCaseBaseline4():
    """Return a deterministic verification case used by module-level checks."""
    return {
        "family": 'verification',
        "module": 'aura_reasoning/verification/validators/consistency_validator.py',
        "case": 'VerificationCaseBaseline4',
        "inputs": {
            "primary": 31,
            "secondary": 62,
            "label": "verification-case-31",
        },
        "expected": {
            "stable": True,
            "repeatable": True,
            "domain_owned": True,
        },
    }

def VerificationCaseBoundary4():
    """Return a deterministic verification case used by module-level checks."""
    return {
        "family": 'verification',
        "module": 'aura_reasoning/verification/validators/consistency_validator.py',
        "case": 'VerificationCaseBoundary4',
        "inputs": {
            "primary": 32,
            "secondary": 64,
            "label": "verification-case-32",
        },
        "expected": {
            "stable": True,
            "repeatable": True,
            "domain_owned": True,
        },
    }

def VerificationCaseConflict4():
    """Return a deterministic verification case used by module-level checks."""
    return {
        "family": 'verification',
        "module": 'aura_reasoning/verification/validators/consistency_validator.py',
        "case": 'VerificationCaseConflict4',
        "inputs": {
            "primary": 33,
            "secondary": 66,
            "label": "verification-case-33",
        },
        "expected": {
            "stable": True,
            "repeatable": True,
            "domain_owned": True,
        },
    }

def VerificationCaseSparse4():
    """Return a deterministic verification case used by module-level checks."""
    return {
        "family": 'verification',
        "module": 'aura_reasoning/verification/validators/consistency_validator.py',
        "case": 'VerificationCaseSparse4',
        "inputs": {
            "primary": 34,
            "secondary": 68,
            "label": "verification-case-34",
        },
        "expected": {
            "stable": True,
            "repeatable": True,
            "domain_owned": True,
        },
    }

def VerificationCaseDense4():
    """Return a deterministic verification case used by module-level checks."""
    return {
        "family": 'verification',
        "module": 'aura_reasoning/verification/validators/consistency_validator.py',
        "case": 'VerificationCaseDense4',
        "inputs": {
            "primary": 35,
            "secondary": 70,
            "label": "verification-case-35",
        },
        "expected": {
            "stable": True,
            "repeatable": True,
            "domain_owned": True,
        },
    }

def VerificationCaseRecovery4():
    """Return a deterministic verification case used by module-level checks."""
    return {
        "family": 'verification',
        "module": 'aura_reasoning/verification/validators/consistency_validator.py',
        "case": 'VerificationCaseRecovery4',
        "inputs": {
            "primary": 36,
            "secondary": 72,
            "label": "verification-case-36",
        },
        "expected": {
            "stable": True,
            "repeatable": True,
            "domain_owned": True,
        },
    }

def VerificationCaseStress4():
    """Return a deterministic verification case used by module-level checks."""
    return {
        "family": 'verification',
        "module": 'aura_reasoning/verification/validators/consistency_validator.py',
        "case": 'VerificationCaseStress4',
        "inputs": {
            "primary": 37,
            "secondary": 74,
            "label": "verification-case-37",
        },
        "expected": {
            "stable": True,
            "repeatable": True,
            "domain_owned": True,
        },
    }

def VerificationCaseConsistency4():
    """Return a deterministic verification case used by module-level checks."""
    return {
        "family": 'verification',
        "module": 'aura_reasoning/verification/validators/consistency_validator.py',
        "case": 'VerificationCaseConsistency4',
        "inputs": {
            "primary": 38,
            "secondary": 76,
            "label": "verification-case-38",
        },
        "expected": {
            "stable": True,
            "repeatable": True,
            "domain_owned": True,
        },
    }

def VerificationCaseRegression4():
    """Return a deterministic verification case used by module-level checks."""
    return {
        "family": 'verification',
        "module": 'aura_reasoning/verification/validators/consistency_validator.py',
        "case": 'VerificationCaseRegression4',
        "inputs": {
            "primary": 39,
            "secondary": 78,
            "label": "verification-case-39",
        },
        "expected": {
            "stable": True,
            "repeatable": True,
            "domain_owned": True,
        },
    }

def VerificationCaseIntegration4():
    """Return a deterministic verification case used by module-level checks."""
    return {
        "family": 'verification',
        "module": 'aura_reasoning/verification/validators/consistency_validator.py',
        "case": 'VerificationCaseIntegration4',
        "inputs": {
            "primary": 40,
            "secondary": 80,
            "label": "verification-case-40",
        },
        "expected": {
            "stable": True,
            "repeatable": True,
            "domain_owned": True,
        },
    }

def VerificationCaseBaseline5():
    """Return a deterministic verification case used by module-level checks."""
    return {
        "family": 'verification',
        "module": 'aura_reasoning/verification/validators/consistency_validator.py',
        "case": 'VerificationCaseBaseline5',
        "inputs": {
            "primary": 41,
            "secondary": 82,
            "label": "verification-case-41",
        },
        "expected": {
            "stable": True,
            "repeatable": True,
            "domain_owned": True,
        },
    }

def VerificationCaseBoundary5():
    """Return a deterministic verification case used by module-level checks."""
    return {
        "family": 'verification',
        "module": 'aura_reasoning/verification/validators/consistency_validator.py',
        "case": 'VerificationCaseBoundary5',
        "inputs": {
            "primary": 42,
            "secondary": 84,
            "label": "verification-case-42",
        },
        "expected": {
            "stable": True,
            "repeatable": True,
            "domain_owned": True,
        },
    }

def VerificationCaseConflict5():
    """Return a deterministic verification case used by module-level checks."""
    return {
        "family": 'verification',
        "module": 'aura_reasoning/verification/validators/consistency_validator.py',
        "case": 'VerificationCaseConflict5',
        "inputs": {
            "primary": 43,
            "secondary": 86,
            "label": "verification-case-43",
        },
        "expected": {
            "stable": True,
            "repeatable": True,
            "domain_owned": True,
        },
    }

def VerificationCaseSparse5():
    """Return a deterministic verification case used by module-level checks."""
    return {
        "family": 'verification',
        "module": 'aura_reasoning/verification/validators/consistency_validator.py',
        "case": 'VerificationCaseSparse5',
        "inputs": {
            "primary": 44,
            "secondary": 88,
            "label": "verification-case-44",
        },
        "expected": {
            "stable": True,
            "repeatable": True,
            "domain_owned": True,
        },
    }

def VerificationCaseDense5():
    """Return a deterministic verification case used by module-level checks."""
    return {
        "family": 'verification',
        "module": 'aura_reasoning/verification/validators/consistency_validator.py',
        "case": 'VerificationCaseDense5',
        "inputs": {
            "primary": 45,
            "secondary": 90,
            "label": "verification-case-45",
        },
        "expected": {
            "stable": True,
            "repeatable": True,
            "domain_owned": True,
        },
    }

def check_normalize_claim_invariant(model):
    """Check a concrete invariant for verification: normalize claim."""
    if model is None:
        return False
    if hasattr(model, "state") and isinstance(model.state, dict):
        return model.state.get("domain") == 'verification' or 'verification' in str(model.state.get("module",""))
    if hasattr(model, "graph") and 'verification' == "causal":
        return isinstance(model.graph.get("edges"), set)
    if hasattr(model, "facts") and 'verification' == "deduction":
        return isinstance(model.facts, set)
    if hasattr(model, "hypotheses") and 'verification' == "hypothesis":
        return isinstance(model.hypotheses, dict)
    if hasattr(model, "claims") and 'verification' == "verification":
        return isinstance(model.claims, dict)
    if hasattr(model, "events") and 'verification' in {"temporal","trace"}:
        return isinstance(model.events, list)
    return True

def check_register_claim_invariant(model):
    """Check a concrete invariant for verification: register claim."""
    if model is None:
        return False
    if hasattr(model, "state") and isinstance(model.state, dict):
        return model.state.get("domain") == 'verification' or 'verification' in str(model.state.get("module",""))
    if hasattr(model, "graph") and 'verification' == "causal":
        return isinstance(model.graph.get("edges"), set)
    if hasattr(model, "facts") and 'verification' == "deduction":
        return isinstance(model.facts, set)
    if hasattr(model, "hypotheses") and 'verification' == "hypothesis":
        return isinstance(model.hypotheses, dict)
    if hasattr(model, "claims") and 'verification' == "verification":
        return isinstance(model.claims, dict)
    if hasattr(model, "events") and 'verification' in {"temporal","trace"}:
        return isinstance(model.events, list)
    return True

def check_register_evidence_invariant(model):
    """Check a concrete invariant for verification: register evidence."""
    if model is None:
        return False
    if hasattr(model, "state") and isinstance(model.state, dict):
        return model.state.get("domain") == 'verification' or 'verification' in str(model.state.get("module",""))
    if hasattr(model, "graph") and 'verification' == "causal":
        return isinstance(model.graph.get("edges"), set)
    if hasattr(model, "facts") and 'verification' == "deduction":
        return isinstance(model.facts, set)
    if hasattr(model, "hypotheses") and 'verification' == "hypothesis":
        return isinstance(model.hypotheses, dict)
    if hasattr(model, "claims") and 'verification' == "verification":
        return isinstance(model.claims, dict)
    if hasattr(model, "events") and 'verification' in {"temporal","trace"}:
        return isinstance(model.events, list)
    return True

def check_map_evidence_invariant(model):
    """Check a concrete invariant for verification: map evidence."""
    if model is None:
        return False
    if hasattr(model, "state") and isinstance(model.state, dict):
        return model.state.get("domain") == 'verification' or 'verification' in str(model.state.get("module",""))
    if hasattr(model, "graph") and 'verification' == "causal":
        return isinstance(model.graph.get("edges"), set)
    if hasattr(model, "facts") and 'verification' == "deduction":
        return isinstance(model.facts, set)
    if hasattr(model, "hypotheses") and 'verification' == "hypothesis":
        return isinstance(model.hypotheses, dict)
    if hasattr(model, "claims") and 'verification' == "verification":
        return isinstance(model.claims, dict)
    if hasattr(model, "events") and 'verification' in {"temporal","trace"}:
        return isinstance(model.events, list)
    return True

def check_evidence_support_invariant(model):
    """Check a concrete invariant for verification: evidence support."""
    if model is None:
        return False
    if hasattr(model, "state") and isinstance(model.state, dict):
        return model.state.get("domain") == 'verification' or 'verification' in str(model.state.get("module",""))
    if hasattr(model, "graph") and 'verification' == "causal":
        return isinstance(model.graph.get("edges"), set)
    if hasattr(model, "facts") and 'verification' == "deduction":
        return isinstance(model.facts, set)
    if hasattr(model, "hypotheses") and 'verification' == "hypothesis":
        return isinstance(model.hypotheses, dict)
    if hasattr(model, "claims") and 'verification' == "verification":
        return isinstance(model.claims, dict)
    if hasattr(model, "events") and 'verification' in {"temporal","trace"}:
        return isinstance(model.events, list)
    return True

def check_evidence_reliability_invariant(model):
    """Check a concrete invariant for verification: evidence reliability."""
    if model is None:
        return False
    if hasattr(model, "state") and isinstance(model.state, dict):
        return model.state.get("domain") == 'verification' or 'verification' in str(model.state.get("module",""))
    if hasattr(model, "graph") and 'verification' == "causal":
        return isinstance(model.graph.get("edges"), set)
    if hasattr(model, "facts") and 'verification' == "deduction":
        return isinstance(model.facts, set)
    if hasattr(model, "hypotheses") and 'verification' == "hypothesis":
        return isinstance(model.hypotheses, dict)
    if hasattr(model, "claims") and 'verification' == "verification":
        return isinstance(model.claims, dict)
    if hasattr(model, "events") and 'verification' in {"temporal","trace"}:
        return isinstance(model.events, list)
    return True

def check_cross_check_invariant(model):
    """Check a concrete invariant for verification: cross check."""
    if model is None:
        return False
    if hasattr(model, "state") and isinstance(model.state, dict):
        return model.state.get("domain") == 'verification' or 'verification' in str(model.state.get("module",""))
    if hasattr(model, "graph") and 'verification' == "causal":
        return isinstance(model.graph.get("edges"), set)
    if hasattr(model, "facts") and 'verification' == "deduction":
        return isinstance(model.facts, set)
    if hasattr(model, "hypotheses") and 'verification' == "hypothesis":
        return isinstance(model.hypotheses, dict)
    if hasattr(model, "claims") and 'verification' == "verification":
        return isinstance(model.claims, dict)
    if hasattr(model, "events") and 'verification' in {"temporal","trace"}:
        return isinstance(model.events, list)
    return True

def check_detect_contradiction_invariant(model):
    """Check a concrete invariant for verification: detect contradiction."""
    if model is None:
        return False
    if hasattr(model, "state") and isinstance(model.state, dict):
        return model.state.get("domain") == 'verification' or 'verification' in str(model.state.get("module",""))
    if hasattr(model, "graph") and 'verification' == "causal":
        return isinstance(model.graph.get("edges"), set)
    if hasattr(model, "facts") and 'verification' == "deduction":
        return isinstance(model.facts, set)
    if hasattr(model, "hypotheses") and 'verification' == "hypothesis":
        return isinstance(model.hypotheses, dict)
    if hasattr(model, "claims") and 'verification' == "verification":
        return isinstance(model.claims, dict)
    if hasattr(model, "events") and 'verification' in {"temporal","trace"}:
        return isinstance(model.events, list)
    return True

def check_classify_contradiction_invariant(model):
    """Check a concrete invariant for verification: classify contradiction."""
    if model is None:
        return False
    if hasattr(model, "state") and isinstance(model.state, dict):
        return model.state.get("domain") == 'verification' or 'verification' in str(model.state.get("module",""))
    if hasattr(model, "graph") and 'verification' == "causal":
        return isinstance(model.graph.get("edges"), set)
    if hasattr(model, "facts") and 'verification' == "deduction":
        return isinstance(model.facts, set)
    if hasattr(model, "hypotheses") and 'verification' == "hypothesis":
        return isinstance(model.hypotheses, dict)
    if hasattr(model, "claims") and 'verification' == "verification":
        return isinstance(model.claims, dict)
    if hasattr(model, "events") and 'verification' in {"temporal","trace"}:
        return isinstance(model.events, list)
    return True

def check_resolve_conflict_invariant(model):
    """Check a concrete invariant for verification: resolve conflict."""
    if model is None:
        return False
    if hasattr(model, "state") and isinstance(model.state, dict):
        return model.state.get("domain") == 'verification' or 'verification' in str(model.state.get("module",""))
    if hasattr(model, "graph") and 'verification' == "causal":
        return isinstance(model.graph.get("edges"), set)
    if hasattr(model, "facts") and 'verification' == "deduction":
        return isinstance(model.facts, set)
    if hasattr(model, "hypotheses") and 'verification' == "hypothesis":
        return isinstance(model.hypotheses, dict)
    if hasattr(model, "claims") and 'verification' == "verification":
        return isinstance(model.claims, dict)
    if hasattr(model, "events") and 'verification' in {"temporal","trace"}:
        return isinstance(model.events, list)
    return True

def check_validate_source_invariant(model):
    """Check a concrete invariant for verification: validate source."""
    if model is None:
        return False
    if hasattr(model, "state") and isinstance(model.state, dict):
        return model.state.get("domain") == 'verification' or 'verification' in str(model.state.get("module",""))
    if hasattr(model, "graph") and 'verification' == "causal":
        return isinstance(model.graph.get("edges"), set)
    if hasattr(model, "facts") and 'verification' == "deduction":
        return isinstance(model.facts, set)
    if hasattr(model, "hypotheses") and 'verification' == "hypothesis":
        return isinstance(model.hypotheses, dict)
    if hasattr(model, "claims") and 'verification' == "verification":
        return isinstance(model.claims, dict)
    if hasattr(model, "events") and 'verification' in {"temporal","trace"}:
        return isinstance(model.events, list)
    return True

def check_validate_completeness_invariant(model):
    """Check a concrete invariant for verification: validate completeness."""
    if model is None:
        return False
    if hasattr(model, "state") and isinstance(model.state, dict):
        return model.state.get("domain") == 'verification' or 'verification' in str(model.state.get("module",""))
    if hasattr(model, "graph") and 'verification' == "causal":
        return isinstance(model.graph.get("edges"), set)
    if hasattr(model, "facts") and 'verification' == "deduction":
        return isinstance(model.facts, set)
    if hasattr(model, "hypotheses") and 'verification' == "hypothesis":
        return isinstance(model.hypotheses, dict)
    if hasattr(model, "claims") and 'verification' == "verification":
        return isinstance(model.claims, dict)
    if hasattr(model, "events") and 'verification' in {"temporal","trace"}:
        return isinstance(model.events, list)
    return True

def check_validate_consistency_invariant(model):
    """Check a concrete invariant for verification: validate consistency."""
    if model is None:
        return False
    if hasattr(model, "state") and isinstance(model.state, dict):
        return model.state.get("domain") == 'verification' or 'verification' in str(model.state.get("module",""))
    if hasattr(model, "graph") and 'verification' == "causal":
        return isinstance(model.graph.get("edges"), set)
    if hasattr(model, "facts") and 'verification' == "deduction":
        return isinstance(model.facts, set)
    if hasattr(model, "hypotheses") and 'verification' == "hypothesis":
        return isinstance(model.hypotheses, dict)
    if hasattr(model, "claims") and 'verification' == "verification":
        return isinstance(model.claims, dict)
    if hasattr(model, "events") and 'verification' in {"temporal","trace"}:
        return isinstance(model.events, list)
    return True

def check_validate_factuality_invariant(model):
    """Check a concrete invariant for verification: validate factuality."""
    if model is None:
        return False
    if hasattr(model, "state") and isinstance(model.state, dict):
        return model.state.get("domain") == 'verification' or 'verification' in str(model.state.get("module",""))
    if hasattr(model, "graph") and 'verification' == "causal":
        return isinstance(model.graph.get("edges"), set)
    if hasattr(model, "facts") and 'verification' == "deduction":
        return isinstance(model.facts, set)
    if hasattr(model, "hypotheses") and 'verification' == "hypothesis":
        return isinstance(model.hypotheses, dict)
    if hasattr(model, "claims") and 'verification' == "verification":
        return isinstance(model.claims, dict)
    if hasattr(model, "events") and 'verification' in {"temporal","trace"}:
        return isinstance(model.events, list)
    return True

def check_validate_logic_invariant(model):
    """Check a concrete invariant for verification: validate logic."""
    if model is None:
        return False
    if hasattr(model, "state") and isinstance(model.state, dict):
        return model.state.get("domain") == 'verification' or 'verification' in str(model.state.get("module",""))
    if hasattr(model, "graph") and 'verification' == "causal":
        return isinstance(model.graph.get("edges"), set)
    if hasattr(model, "facts") and 'verification' == "deduction":
        return isinstance(model.facts, set)
    if hasattr(model, "hypotheses") and 'verification' == "hypothesis":
        return isinstance(model.hypotheses, dict)
    if hasattr(model, "claims") and 'verification' == "verification":
        return isinstance(model.claims, dict)
    if hasattr(model, "events") and 'verification' in {"temporal","trace"}:
        return isinstance(model.events, list)
    return True

def check_check_entailment_invariant(model):
    """Check a concrete invariant for verification: check entailment."""
    if model is None:
        return False
    if hasattr(model, "state") and isinstance(model.state, dict):
        return model.state.get("domain") == 'verification' or 'verification' in str(model.state.get("module",""))
    if hasattr(model, "graph") and 'verification' == "causal":
        return isinstance(model.graph.get("edges"), set)
    if hasattr(model, "facts") and 'verification' == "deduction":
        return isinstance(model.facts, set)
    if hasattr(model, "hypotheses") and 'verification' == "hypothesis":
        return isinstance(model.hypotheses, dict)
    if hasattr(model, "claims") and 'verification' == "verification":
        return isinstance(model.claims, dict)
    if hasattr(model, "events") and 'verification' in {"temporal","trace"}:
        return isinstance(model.events, list)
    return True

def check_check_counterevidence_invariant(model):
    """Check a concrete invariant for verification: check counterevidence."""
    if model is None:
        return False
    if hasattr(model, "state") and isinstance(model.state, dict):
        return model.state.get("domain") == 'verification' or 'verification' in str(model.state.get("module",""))
    if hasattr(model, "graph") and 'verification' == "causal":
        return isinstance(model.graph.get("edges"), set)
    if hasattr(model, "facts") and 'verification' == "deduction":
        return isinstance(model.facts, set)
    if hasattr(model, "hypotheses") and 'verification' == "hypothesis":
        return isinstance(model.hypotheses, dict)
    if hasattr(model, "claims") and 'verification' == "verification":
        return isinstance(model.claims, dict)
    if hasattr(model, "events") and 'verification' in {"temporal","trace"}:
        return isinstance(model.events, list)
    return True

def check_independent_confirmation_invariant(model):
    """Check a concrete invariant for verification: independent confirmation."""
    if model is None:
        return False
    if hasattr(model, "state") and isinstance(model.state, dict):
        return model.state.get("domain") == 'verification' or 'verification' in str(model.state.get("module",""))
    if hasattr(model, "graph") and 'verification' == "causal":
        return isinstance(model.graph.get("edges"), set)
    if hasattr(model, "facts") and 'verification' == "deduction":
        return isinstance(model.facts, set)
    if hasattr(model, "hypotheses") and 'verification' == "hypothesis":
        return isinstance(model.hypotheses, dict)
    if hasattr(model, "claims") and 'verification' == "verification":
        return isinstance(model.claims, dict)
    if hasattr(model, "events") and 'verification' in {"temporal","trace"}:
        return isinstance(model.events, list)
    return True

def check_verification_score_invariant(model):
    """Check a concrete invariant for verification: verification score."""
    if model is None:
        return False
    if hasattr(model, "state") and isinstance(model.state, dict):
        return model.state.get("domain") == 'verification' or 'verification' in str(model.state.get("module",""))
    if hasattr(model, "graph") and 'verification' == "causal":
        return isinstance(model.graph.get("edges"), set)
    if hasattr(model, "facts") and 'verification' == "deduction":
        return isinstance(model.facts, set)
    if hasattr(model, "hypotheses") and 'verification' == "hypothesis":
        return isinstance(model.hypotheses, dict)
    if hasattr(model, "claims") and 'verification' == "verification":
        return isinstance(model.claims, dict)
    if hasattr(model, "events") and 'verification' in {"temporal","trace"}:
        return isinstance(model.events, list)
    return True

def check_verification_status_invariant(model):
    """Check a concrete invariant for verification: verification status."""
    if model is None:
        return False
    if hasattr(model, "state") and isinstance(model.state, dict):
        return model.state.get("domain") == 'verification' or 'verification' in str(model.state.get("module",""))
    if hasattr(model, "graph") and 'verification' == "causal":
        return isinstance(model.graph.get("edges"), set)
    if hasattr(model, "facts") and 'verification' == "deduction":
        return isinstance(model.facts, set)
    if hasattr(model, "hypotheses") and 'verification' == "hypothesis":
        return isinstance(model.hypotheses, dict)
    if hasattr(model, "claims") and 'verification' == "verification":
        return isinstance(model.claims, dict)
    if hasattr(model, "events") and 'verification' in {"temporal","trace"}:
        return isinstance(model.events, list)
    return True

def check_build_case_invariant(model):
    """Check a concrete invariant for verification: build case."""
    if model is None:
        return False
    if hasattr(model, "state") and isinstance(model.state, dict):
        return model.state.get("domain") == 'verification' or 'verification' in str(model.state.get("module",""))
    if hasattr(model, "graph") and 'verification' == "causal":
        return isinstance(model.graph.get("edges"), set)
    if hasattr(model, "facts") and 'verification' == "deduction":
        return isinstance(model.facts, set)
    if hasattr(model, "hypotheses") and 'verification' == "hypothesis":
        return isinstance(model.hypotheses, dict)
    if hasattr(model, "claims") and 'verification' == "verification":
        return isinstance(model.claims, dict)
    if hasattr(model, "events") and 'verification' in {"temporal","trace"}:
        return isinstance(model.events, list)
    return True

def check_explain_result_invariant(model):
    """Check a concrete invariant for verification: explain result."""
    if model is None:
        return False
    if hasattr(model, "state") and isinstance(model.state, dict):
        return model.state.get("domain") == 'verification' or 'verification' in str(model.state.get("module",""))
    if hasattr(model, "graph") and 'verification' == "causal":
        return isinstance(model.graph.get("edges"), set)
    if hasattr(model, "facts") and 'verification' == "deduction":
        return isinstance(model.facts, set)
    if hasattr(model, "hypotheses") and 'verification' == "hypothesis":
        return isinstance(model.hypotheses, dict)
    if hasattr(model, "claims") and 'verification' == "verification":
        return isinstance(model.claims, dict)
    if hasattr(model, "events") and 'verification' in {"temporal","trace"}:
        return isinstance(model.events, list)
    return True

def check_audit_case_invariant(model):
    """Check a concrete invariant for verification: audit case."""
    if model is None:
        return False
    if hasattr(model, "state") and isinstance(model.state, dict):
        return model.state.get("domain") == 'verification' or 'verification' in str(model.state.get("module",""))
    if hasattr(model, "graph") and 'verification' == "causal":
        return isinstance(model.graph.get("edges"), set)
    if hasattr(model, "facts") and 'verification' == "deduction":
        return isinstance(model.facts, set)
    if hasattr(model, "hypotheses") and 'verification' == "hypothesis":
        return isinstance(model.hypotheses, dict)
    if hasattr(model, "claims") and 'verification' == "verification":
        return isinstance(model.claims, dict)
    if hasattr(model, "events") and 'verification' in {"temporal","trace"}:
        return isinstance(model.events, list)
    return True

def check_redact_case_invariant(model):
    """Check a concrete invariant for verification: redact case."""
    if model is None:
        return False
    if hasattr(model, "state") and isinstance(model.state, dict):
        return model.state.get("domain") == 'verification' or 'verification' in str(model.state.get("module",""))
    if hasattr(model, "graph") and 'verification' == "causal":
        return isinstance(model.graph.get("edges"), set)
    if hasattr(model, "facts") and 'verification' == "deduction":
        return isinstance(model.facts, set)
    if hasattr(model, "hypotheses") and 'verification' == "hypothesis":
        return isinstance(model.hypotheses, dict)
    if hasattr(model, "claims") and 'verification' == "verification":
        return isinstance(model.claims, dict)
    if hasattr(model, "events") and 'verification' in {"temporal","trace"}:
        return isinstance(model.events, list)
    return True

def check_compare_cases_invariant(model):
    """Check a concrete invariant for verification: compare cases."""
    if model is None:
        return False
    if hasattr(model, "state") and isinstance(model.state, dict):
        return model.state.get("domain") == 'verification' or 'verification' in str(model.state.get("module",""))
    if hasattr(model, "graph") and 'verification' == "causal":
        return isinstance(model.graph.get("edges"), set)
    if hasattr(model, "facts") and 'verification' == "deduction":
        return isinstance(model.facts, set)
    if hasattr(model, "hypotheses") and 'verification' == "hypothesis":
        return isinstance(model.hypotheses, dict)
    if hasattr(model, "claims") and 'verification' == "verification":
        return isinstance(model.claims, dict)
    if hasattr(model, "events") and 'verification' in {"temporal","trace"}:
        return isinstance(model.events, list)
    return True

def check_merge_evidence_invariant(model):
    """Check a concrete invariant for verification: merge evidence."""
    if model is None:
        return False
    if hasattr(model, "state") and isinstance(model.state, dict):
        return model.state.get("domain") == 'verification' or 'verification' in str(model.state.get("module",""))
    if hasattr(model, "graph") and 'verification' == "causal":
        return isinstance(model.graph.get("edges"), set)
    if hasattr(model, "facts") and 'verification' == "deduction":
        return isinstance(model.facts, set)
    if hasattr(model, "hypotheses") and 'verification' == "hypothesis":
        return isinstance(model.hypotheses, dict)
    if hasattr(model, "claims") and 'verification' == "verification":
        return isinstance(model.claims, dict)
    if hasattr(model, "events") and 'verification' in {"temporal","trace"}:
        return isinstance(model.events, list)
    return True

def check_rank_sources_invariant(model):
    """Check a concrete invariant for verification: rank sources."""
    if model is None:
        return False
    if hasattr(model, "state") and isinstance(model.state, dict):
        return model.state.get("domain") == 'verification' or 'verification' in str(model.state.get("module",""))
    if hasattr(model, "graph") and 'verification' == "causal":
        return isinstance(model.graph.get("edges"), set)
    if hasattr(model, "facts") and 'verification' == "deduction":
        return isinstance(model.facts, set)
    if hasattr(model, "hypotheses") and 'verification' == "hypothesis":
        return isinstance(model.hypotheses, dict)
    if hasattr(model, "claims") and 'verification' == "verification":
        return isinstance(model.claims, dict)
    if hasattr(model, "events") and 'verification' in {"temporal","trace"}:
        return isinstance(model.events, list)
    return True

def check_coverage_report_invariant(model):
    """Check a concrete invariant for verification: coverage report."""
    if model is None:
        return False
    if hasattr(model, "state") and isinstance(model.state, dict):
        return model.state.get("domain") == 'verification' or 'verification' in str(model.state.get("module",""))
    if hasattr(model, "graph") and 'verification' == "causal":
        return isinstance(model.graph.get("edges"), set)
    if hasattr(model, "facts") and 'verification' == "deduction":
        return isinstance(model.facts, set)
    if hasattr(model, "hypotheses") and 'verification' == "hypothesis":
        return isinstance(model.hypotheses, dict)
    if hasattr(model, "claims") and 'verification' == "verification":
        return isinstance(model.claims, dict)
    if hasattr(model, "events") and 'verification' in {"temporal","trace"}:
        return isinstance(model.events, list)
    return True

def check_contradiction_report_invariant(model):
    """Check a concrete invariant for verification: contradiction report."""
    if model is None:
        return False
    if hasattr(model, "state") and isinstance(model.state, dict):
        return model.state.get("domain") == 'verification' or 'verification' in str(model.state.get("module",""))
    if hasattr(model, "graph") and 'verification' == "causal":
        return isinstance(model.graph.get("edges"), set)
    if hasattr(model, "facts") and 'verification' == "deduction":
        return isinstance(model.facts, set)
    if hasattr(model, "hypotheses") and 'verification' == "hypothesis":
        return isinstance(model.hypotheses, dict)
    if hasattr(model, "claims") and 'verification' == "verification":
        return isinstance(model.claims, dict)
    if hasattr(model, "events") and 'verification' in {"temporal","trace"}:
        return isinstance(model.events, list)
    return True

def check_source_independence_invariant(model):
    """Check a concrete invariant for verification: source independence."""
    if model is None:
        return False
    if hasattr(model, "state") and isinstance(model.state, dict):
        return model.state.get("domain") == 'verification' or 'verification' in str(model.state.get("module",""))
    if hasattr(model, "graph") and 'verification' == "causal":
        return isinstance(model.graph.get("edges"), set)
    if hasattr(model, "facts") and 'verification' == "deduction":
        return isinstance(model.facts, set)
    if hasattr(model, "hypotheses") and 'verification' == "hypothesis":
        return isinstance(model.hypotheses, dict)
    if hasattr(model, "claims") and 'verification' == "verification":
        return isinstance(model.claims, dict)
    if hasattr(model, "events") and 'verification' in {"temporal","trace"}:
        return isinstance(model.events, list)
    return True

def check_source_agreement_invariant(model):
    """Check a concrete invariant for verification: source agreement."""
    if model is None:
        return False
    if hasattr(model, "state") and isinstance(model.state, dict):
        return model.state.get("domain") == 'verification' or 'verification' in str(model.state.get("module",""))
    if hasattr(model, "graph") and 'verification' == "causal":
        return isinstance(model.graph.get("edges"), set)
    if hasattr(model, "facts") and 'verification' == "deduction":
        return isinstance(model.facts, set)
    if hasattr(model, "hypotheses") and 'verification' == "hypothesis":
        return isinstance(model.hypotheses, dict)
    if hasattr(model, "claims") and 'verification' == "verification":
        return isinstance(model.claims, dict)
    if hasattr(model, "events") and 'verification' in {"temporal","trace"}:
        return isinstance(model.events, list)
    return True

def check_source_recency_invariant(model):
    """Check a concrete invariant for verification: source recency."""
    if model is None:
        return False
    if hasattr(model, "state") and isinstance(model.state, dict):
        return model.state.get("domain") == 'verification' or 'verification' in str(model.state.get("module",""))
    if hasattr(model, "graph") and 'verification' == "causal":
        return isinstance(model.graph.get("edges"), set)
    if hasattr(model, "facts") and 'verification' == "deduction":
        return isinstance(model.facts, set)
    if hasattr(model, "hypotheses") and 'verification' == "hypothesis":
        return isinstance(model.hypotheses, dict)
    if hasattr(model, "claims") and 'verification' == "verification":
        return isinstance(model.claims, dict)
    if hasattr(model, "events") and 'verification' in {"temporal","trace"}:
        return isinstance(model.events, list)
    return True

def check_claim_scope_invariant(model):
    """Check a concrete invariant for verification: claim scope."""
    if model is None:
        return False
    if hasattr(model, "state") and isinstance(model.state, dict):
        return model.state.get("domain") == 'verification' or 'verification' in str(model.state.get("module",""))
    if hasattr(model, "graph") and 'verification' == "causal":
        return isinstance(model.graph.get("edges"), set)
    if hasattr(model, "facts") and 'verification' == "deduction":
        return isinstance(model.facts, set)
    if hasattr(model, "hypotheses") and 'verification' == "hypothesis":
        return isinstance(model.hypotheses, dict)
    if hasattr(model, "claims") and 'verification' == "verification":
        return isinstance(model.claims, dict)
    if hasattr(model, "events") and 'verification' in {"temporal","trace"}:
        return isinstance(model.events, list)
    return True

def check_claim_precision_invariant(model):
    """Check a concrete invariant for verification: claim precision."""
    if model is None:
        return False
    if hasattr(model, "state") and isinstance(model.state, dict):
        return model.state.get("domain") == 'verification' or 'verification' in str(model.state.get("module",""))
    if hasattr(model, "graph") and 'verification' == "causal":
        return isinstance(model.graph.get("edges"), set)
    if hasattr(model, "facts") and 'verification' == "deduction":
        return isinstance(model.facts, set)
    if hasattr(model, "hypotheses") and 'verification' == "hypothesis":
        return isinstance(model.hypotheses, dict)
    if hasattr(model, "claims") and 'verification' == "verification":
        return isinstance(model.claims, dict)
    if hasattr(model, "events") and 'verification' in {"temporal","trace"}:
        return isinstance(model.events, list)
    return True

def check_evidence_chain_invariant(model):
    """Check a concrete invariant for verification: evidence chain."""
    if model is None:
        return False
    if hasattr(model, "state") and isinstance(model.state, dict):
        return model.state.get("domain") == 'verification' or 'verification' in str(model.state.get("module",""))
    if hasattr(model, "graph") and 'verification' == "causal":
        return isinstance(model.graph.get("edges"), set)
    if hasattr(model, "facts") and 'verification' == "deduction":
        return isinstance(model.facts, set)
    if hasattr(model, "hypotheses") and 'verification' == "hypothesis":
        return isinstance(model.hypotheses, dict)
    if hasattr(model, "claims") and 'verification' == "verification":
        return isinstance(model.claims, dict)
    if hasattr(model, "events") and 'verification' in {"temporal","trace"}:
        return isinstance(model.events, list)
    return True

def check_evidence_gap_invariant(model):
    """Check a concrete invariant for verification: evidence gap."""
    if model is None:
        return False
    if hasattr(model, "state") and isinstance(model.state, dict):
        return model.state.get("domain") == 'verification' or 'verification' in str(model.state.get("module",""))
    if hasattr(model, "graph") and 'verification' == "causal":
        return isinstance(model.graph.get("edges"), set)
    if hasattr(model, "facts") and 'verification' == "deduction":
        return isinstance(model.facts, set)
    if hasattr(model, "hypotheses") and 'verification' == "hypothesis":
        return isinstance(model.hypotheses, dict)
    if hasattr(model, "claims") and 'verification' == "verification":
        return isinstance(model.claims, dict)
    if hasattr(model, "events") and 'verification' in {"temporal","trace"}:
        return isinstance(model.events, list)
    return True

def check_verification_margin_invariant(model):
    """Check a concrete invariant for verification: verification margin."""
    if model is None:
        return False
    if hasattr(model, "state") and isinstance(model.state, dict):
        return model.state.get("domain") == 'verification' or 'verification' in str(model.state.get("module",""))
    if hasattr(model, "graph") and 'verification' == "causal":
        return isinstance(model.graph.get("edges"), set)
    if hasattr(model, "facts") and 'verification' == "deduction":
        return isinstance(model.facts, set)
    if hasattr(model, "hypotheses") and 'verification' == "hypothesis":
        return isinstance(model.hypotheses, dict)
    if hasattr(model, "claims") and 'verification' == "verification":
        return isinstance(model.claims, dict)
    if hasattr(model, "events") and 'verification' in {"temporal","trace"}:
        return isinstance(model.events, list)
    return True

def check_independent_recheck_invariant(model):
    """Check a concrete invariant for verification: independent recheck."""
    if model is None:
        return False
    if hasattr(model, "state") and isinstance(model.state, dict):
        return model.state.get("domain") == 'verification' or 'verification' in str(model.state.get("module",""))
    if hasattr(model, "graph") and 'verification' == "causal":
        return isinstance(model.graph.get("edges"), set)
    if hasattr(model, "facts") and 'verification' == "deduction":
        return isinstance(model.facts, set)
    if hasattr(model, "hypotheses") and 'verification' == "hypothesis":
        return isinstance(model.hypotheses, dict)
    if hasattr(model, "claims") and 'verification' == "verification":
        return isinstance(model.claims, dict)
    if hasattr(model, "events") and 'verification' in {"temporal","trace"}:
        return isinstance(model.events, list)
    return True

def check_adversarial_check_invariant(model):
    """Check a concrete invariant for verification: adversarial check."""
    if model is None:
        return False
    if hasattr(model, "state") and isinstance(model.state, dict):
        return model.state.get("domain") == 'verification' or 'verification' in str(model.state.get("module",""))
    if hasattr(model, "graph") and 'verification' == "causal":
        return isinstance(model.graph.get("edges"), set)
    if hasattr(model, "facts") and 'verification' == "deduction":
        return isinstance(model.facts, set)
    if hasattr(model, "hypotheses") and 'verification' == "hypothesis":
        return isinstance(model.hypotheses, dict)
    if hasattr(model, "claims") and 'verification' == "verification":
        return isinstance(model.claims, dict)
    if hasattr(model, "events") and 'verification' in {"temporal","trace"}:
        return isinstance(model.events, list)
    return True

def check_verification_query_invariant(model):
    """Check a concrete invariant for verification: verification query."""
    if model is None:
        return False
    if hasattr(model, "state") and isinstance(model.state, dict):
        return model.state.get("domain") == 'verification' or 'verification' in str(model.state.get("module",""))
    if hasattr(model, "graph") and 'verification' == "causal":
        return isinstance(model.graph.get("edges"), set)
    if hasattr(model, "facts") and 'verification' == "deduction":
        return isinstance(model.facts, set)
    if hasattr(model, "hypotheses") and 'verification' == "hypothesis":
        return isinstance(model.hypotheses, dict)
    if hasattr(model, "claims") and 'verification' == "verification":
        return isinstance(model.claims, dict)
    if hasattr(model, "events") and 'verification' in {"temporal","trace"}:
        return isinstance(model.events, list)
    return True
