REGISTRY = {}

def register(name: str, factory):
    REGISTRY[name] = factory

def get(name: str):
    return REGISTRY.get(name)
