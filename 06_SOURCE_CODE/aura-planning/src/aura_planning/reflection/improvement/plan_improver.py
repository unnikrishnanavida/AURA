class PlanImprover:
    def improve(self,plan,alternatives,score):
        candidates=(plan,)+tuple(alternatives)
        return max(candidates,key=score,default=plan)
