def resolve_inputs(action, supplied):
    missing=set(action.inputs)-set(supplied)
    if missing: raise ValueError(f"missing inputs: {sorted(missing)}")
    return {k:supplied[k] for k in action.inputs}
