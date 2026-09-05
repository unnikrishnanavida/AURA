class OutcomeWriter:
    def record(self,memory,outcome): return type(memory)(memory.plan_id,memory.goal_key,memory.plan,outcome)
