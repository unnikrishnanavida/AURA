def detect(action):
    reasons=[]
    if action.risk>=1: reasons.append("risk score outside safe range")
    if action.timeout>3600: reasons.append("timeout exceeds safety limit")
    return reasons
