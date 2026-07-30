from typing import Iterable, List


def ensure_list(x) -> List:
    if x is None:
        return []
    if isinstance(x, list):
        return x
    if isinstance(x, Iterable):
        return list(x)
    return [x]
