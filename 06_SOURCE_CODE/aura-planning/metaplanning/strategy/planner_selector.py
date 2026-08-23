class PlannerSelector:
    def select(self,difficulty):
        score=difficulty.score()
        if difficulty.uncertainty>=.7: return "probabilistic"
        if difficulty.depth>=.7: return "hierarchical"
        if score<=.3: return "a_star"
        if difficulty.branching>=.8: return "beam_search"
        return "a_star"
