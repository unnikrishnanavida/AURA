class StateDistance:
    def __init__(self, weights=None):
        self.weights = dict(weights or {})

    def distance(self, left, right):
        a = getattr(left, "values", left)
        b = getattr(right, "values", right)
        keys = set(a) | set(b)
        total = 0.0
        for key in keys:
            if a.get(key) != b.get(key):
                total += float(self.weights.get(key, 1.0))
        return total
