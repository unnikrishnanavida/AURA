from aura_execution.budgets.reservation import Budget
def test_budget():
 b=Budget(3); assert b.reserve(2); assert not b.reserve(2)
