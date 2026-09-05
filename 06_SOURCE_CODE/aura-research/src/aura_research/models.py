from dataclasses import dataclass, field
from typing import Any

@dataclass(frozen=True)
class Source:
    source_id: str; uri: str; title: str; trust: float; retrieved_at: str

@dataclass(frozen=True)
class Evidence:
    evidence_id: str; source_id: str; text: str; relevance: float; supports: bool = True

@dataclass(frozen=True)
class Claim:
    claim_id: str; statement: str; evidence_ids: tuple[str,...]; confidence: float

@dataclass(frozen=True)
class ResearchResult:
    answer: str; claims: tuple[Claim,...]; uncertainty: str; confidence: float; execution_id: str
