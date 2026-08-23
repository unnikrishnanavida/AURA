from ...search.search_engine import SearchEngine
class ForwardPlanner:
    def __init__(self, actions=(), search=None):
        self.actions=tuple(actions); self.search=search or SearchEngine()
    def successors(self,state):
        for action in self.actions:
            if action.is_applicable(state):
                outcome=action.apply(state)
                if outcome.success: yield action,outcome.state
    def plan(self,initial,goal):
        target=lambda s: goal.matches(s) if hasattr(goal,"matches") else goal(s)
        heuristic=lambda s: len(getattr(goal,"missing",lambda x:{})(s))
        result=self.search.a_star(initial,target,self.successors,heuristic)
        return result
