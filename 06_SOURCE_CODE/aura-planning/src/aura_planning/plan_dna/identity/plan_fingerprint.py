import hashlib,json
def plan_fingerprint(plan):
    actions=[getattr(a,"action_id",repr(a)) for a in getattr(plan,"actions",plan)]
    return hashlib.sha256(json.dumps(actions,sort_keys=True).encode()).hexdigest()
