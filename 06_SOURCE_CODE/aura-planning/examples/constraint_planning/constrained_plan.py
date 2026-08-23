def choose_feasible(candidates,validator):
    return next((candidate for candidate in candidates if not validator(candidate)),None)
