def check_preconditions(action,state,inputs):
    failures=[]
    for key,expected in action.preconditions.items():
        actual=state.get(key)
        if actual!=expected: failures.append((key,expected,actual))
    return failures
