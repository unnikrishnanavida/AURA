def fuse(evidence):
    if not evidence: return 0.0
    yes=sum(max(0,min(1,e.relevance)) for e in evidence if e.supports)
    no=sum(max(0,min(1,e.relevance)) for e in evidence if not e.supports)
    return max(0,min(1,(yes-0.5*no)/len(evidence)))
