from .models.constraint_set import ConstraintSet
from .solving.constraint_solver import ConstraintSolver
from .validation.conflict_detector import ConflictDetector
from .validation.feasibility_checker import FeasibilityChecker
class ConstraintEngine:
    def __init__(self):
        self.solver=ConstraintSolver(); self.conflicts=ConflictDetector(); self.feasibility=FeasibilityChecker()
    def solve(self,candidates,constraints): return self.solver.solve(candidates,constraints)
    def validate(self,constraints,value): return constraints.validate(value)
    def feasible(self,constraints,value): return self.feasibility.is_feasible(constraints,value)
