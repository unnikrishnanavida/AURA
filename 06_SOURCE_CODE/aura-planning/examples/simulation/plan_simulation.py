def simulate(actions,state):
    history=[state]
    for action in actions:
        result=action.apply(state)
        if not result.success: return {"success":False,"history":history}
        state=result.state; history.append(state)
    return {"success":True,"history":history}
