class PreconditionGuard:
    def allow(self, action, state):
        return all(p.evaluate(state) for p in getattr(action,"preconditions",()))
