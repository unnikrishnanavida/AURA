import hashlib,json
def fingerprint(action):
    data=json.dumps({"id":action.action_id,"capability":action.capability,"effects":action.effects},sort_keys=True,default=str)
    return hashlib.sha256(data.encode()).hexdigest()
