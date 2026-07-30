REGISTRY = {}

def register(name: str, validator):
    REGISTRY[name] = validator

def get(name: str):
    return REGISTRY.get(name)
