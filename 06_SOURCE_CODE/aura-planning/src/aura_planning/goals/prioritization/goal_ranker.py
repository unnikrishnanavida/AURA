class GoalRanker:
    def rank(self, goals, now=None):
        return tuple(sorted(
            goals,
            key=lambda g: (
                getattr(g, "priority", 0.0),
                -(g.deadline.timestamp() if getattr(g, "deadline", None) else float("inf")),
            ),
            reverse=True,
        ))
