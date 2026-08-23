class ConstraintConflictDetector:
    def find_conflicts(self, constraints, candidates):
        conflicts=[]
        for candidate in candidates:
            violated=tuple(c for c in constraints if not c.evaluate(candidate))
            if len(violated)>1: conflicts.append((candidate,violated))
        return tuple(conflicts)
