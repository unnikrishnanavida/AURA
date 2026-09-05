class PartialReplanner:
    def replan(self,state,goal,planner,stable_prefix=()):
        result=planner.plan(state,goal)
        if not result or not getattr(result,"success",True): return None
        suffix=result.node.path() if hasattr(result,"node") else result
        return tuple(stable_prefix)+tuple(suffix)
