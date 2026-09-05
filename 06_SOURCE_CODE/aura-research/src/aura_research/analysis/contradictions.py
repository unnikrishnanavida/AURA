def contradiction_score(evidence):
    yes=sum(e.relevance for e in evidence if e.supports); no=sum(e.relevance for e in evidence if not e.supports)
    return 0.0 if yes+no==0 else min(1.0,2*min(yes,no)/(yes+no))
