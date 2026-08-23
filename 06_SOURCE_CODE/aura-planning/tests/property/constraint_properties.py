def test_hard_constraints_reject_invalid_candidates():
    from aura_planning.constraints.models.constraint import Constraint
    from aura_planning.constraints.models.hard_constraint import HardConstraint
    from aura_planning.constraints.models.constraint_set import ConstraintSet
    c=ConstraintSet(hard=(HardConstraint(Constraint("positive",lambda x:x>0)),))
    assert c.validate(-1)
    assert not c.validate(1)
