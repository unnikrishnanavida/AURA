class StateComparator:
    def differences(self, current, target):
        left = getattr(current, "values", current)
        right = getattr(target, "values", target)
        keys = set(left) | set(right)
        return {k: (left.get(k), right.get(k)) for k in keys if left.get(k) != right.get(k)}

    def matches(self, current, target):
        return not self.differences(current, target)

    def goal_distance(self, current, target):
        return len(self.differences(current, target))
