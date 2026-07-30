REGISTRY = {}

def register(event_name: str, handler):
    REGISTRY.setdefault(event_name, []).append(handler)

def get(event_name: str):
    return REGISTRY.get(event_name, [])
