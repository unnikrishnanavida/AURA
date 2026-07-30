_counter = 0


def next_id() -> int:
    global _counter
    _counter += 1
    return _counter
