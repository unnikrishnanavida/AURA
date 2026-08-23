def score(replans,targets):
    if not targets:return 0.0
    return sum(bool(r) for r in replans)/len(targets)
