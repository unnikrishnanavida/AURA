import hashlib
import json


def key(payload): return hashlib.sha256(json.dumps(payload,sort_keys=True,default=str).encode()).hexdigest()
