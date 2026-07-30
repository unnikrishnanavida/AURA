REGISTRY = {}

def register(name: str, service):
    REGISTRY[name] = service

def get(name: str):
    return REGISTRY.get(name)
