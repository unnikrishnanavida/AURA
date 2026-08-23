class ResponsePlanner:
    def respond(self,observation,policies):
        matches=[(priority,action) for predicate,priority,action in policies if predicate(observation)]
        return max(matches,key=lambda x:x[0])[1] if matches else None
