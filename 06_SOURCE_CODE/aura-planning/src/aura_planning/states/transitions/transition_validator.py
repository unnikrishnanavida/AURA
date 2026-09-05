from .transition_model import TransitionModel
def validate_transition(state,transition:TransitionModel):
    return [f"{k} expected {v!r}" for k,v in transition.preconditions.items() if state.values.get(k)!=v]
