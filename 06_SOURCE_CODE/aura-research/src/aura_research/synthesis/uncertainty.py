def uncertainty_message(c):
    if c<=0: return "I do not know; sufficient evidence was not established."
    if c<0.4: return "Evidence is weak or incomplete."
    if c<0.75: return "Evidence is mixed; treat this conclusion cautiously."
    return "Evidence is reasonably consistent."
