REGISTRY = {}

def register(name: str, plugin):
    REGISTRY[name] = plugin

def get(name: str):
    return REGISTRY.get(name)
