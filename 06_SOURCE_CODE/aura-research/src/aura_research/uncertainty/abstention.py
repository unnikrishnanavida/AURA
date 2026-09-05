def should_abstain(c,t=.55): return c<t
def honest_answer(c): return "I do not know based on sufficient evidence." if should_abstain(c) else None
