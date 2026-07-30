REGISTRY = {}

def register(name: str, serializer):
    REGISTRY[name] = serializer

def get(name: str):
    return REGISTRY.get(name)
