def validate_effects(action,state):
    candidate=state
    for effect in action.effects: candidate=effect.apply(candidate)
    return [f"effect failed: {e.variable}" for e in action.effects if candidate.values.get(e.variable)!=e.value]
