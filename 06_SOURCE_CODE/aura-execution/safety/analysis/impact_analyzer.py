def impact(action):
    impacts=[]
    if not action.reversible: impacts.append("irreversible")
    if action.permissions: impacts.append("privileged")
    if action.capability.startswith(("filesystem.","database.")): impacts.append("persistent-state")
    return impacts
