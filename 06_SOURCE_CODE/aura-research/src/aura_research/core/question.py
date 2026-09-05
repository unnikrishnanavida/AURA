from dataclasses import dataclass
@dataclass(frozen=True)
class ResearchQuestion:
    text: str
    scope: str = "general"
    require_citations: bool = True
    freshness_days: int | None = None
