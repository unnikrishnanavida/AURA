import hashlib, json
def execution_fingerprint(action_id, inputs):
    payload=json.dumps({"action":action_id,"inputs":inputs}, sort_keys=True, default=str).encode()
    return hashlib.sha256(payload).hexdigest()
