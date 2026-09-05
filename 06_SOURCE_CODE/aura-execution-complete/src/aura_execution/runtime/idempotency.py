import hashlib,json
def key(action):return hashlib.sha256(json.dumps(action.parameters,sort_keys=True).encode()).hexdigest()
