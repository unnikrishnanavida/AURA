class GoalDistance:
    def estimate(self,state,goal):
        if hasattr(goal,"objectives") and goal.objectives:
            return sum(state.values.get(o.name)!=o.target for o in goal.objectives)
        if hasattr(goal,"description"):
            return 0. if goal.description.lower() in str(state.values).lower() else 1.
        return 1.
