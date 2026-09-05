from uuid import uuid4
from .models import Claim, ResearchResult
from .evidence.fusion import fuse
from .analysis.contradictions import contradiction_score
from .analysis.calibration import calibrate
from .synthesis.uncertainty import uncertainty_message

class ResearchEngine:
    def __init__(self,adapter=None): self.adapter=adapter
    def research(self,q):
        pairs=[] if self.adapter is None else self.adapter.search(q.text)
        evidence=[e for _,e in pairs]
        c=calibrate(fuse(evidence),contradiction_score(evidence))
        claim=Claim("claim-1",q.text,tuple(e.evidence_id for e in evidence),c)
        answer="I do not know." if not evidence else f"Research completed for: {q.text}"
        return ResearchResult(answer,(claim,),uncertainty_message(c),c,str(uuid4()))
