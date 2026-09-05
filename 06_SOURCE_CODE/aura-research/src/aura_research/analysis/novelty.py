def novelty_score(candidate, corpus):
    terms=set(candidate.lower().split()); seen=set().union(*(set(x.lower().split()) for x in corpus)) if corpus else set()
    return 0.0 if not terms else len(terms-seen)/len(terms)
