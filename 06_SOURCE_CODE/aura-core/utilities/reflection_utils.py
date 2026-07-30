import inspect


def get_public_methods(obj):
    return [n for n, v in inspect.getmembers(obj, inspect.isfunction) if not n.startswith("_")]
