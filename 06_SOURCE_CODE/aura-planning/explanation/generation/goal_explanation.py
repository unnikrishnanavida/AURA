class GoalExplanation:
    def explain(self, goal):
        return f"Goal '{goal.description}' has priority {goal.priority:.2f} and state {goal.state.value}."
