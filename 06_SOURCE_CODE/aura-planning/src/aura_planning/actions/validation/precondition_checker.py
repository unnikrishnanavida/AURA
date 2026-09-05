def check_preconditions(action,state):
    return [f"{p.variable} expected {p.expected!r}" for p in action.preconditions if not p.satisfied(state)]
