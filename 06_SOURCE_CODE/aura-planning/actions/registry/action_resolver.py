class ActionResolver:
    def applicable(self,actions,state): return [a for a in actions if a.applicable(state)]
    def cheapest(self,actions): return min(actions,key=lambda a:a.cost,default=None)
