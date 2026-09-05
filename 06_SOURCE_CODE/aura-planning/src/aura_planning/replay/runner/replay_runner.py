class ReplayRunner:
    def run(self,plan,state):
        current=state; events=[]
        for action in getattr(plan,"actions",plan):
            outcome=action.apply(current)
            events.append((getattr(action,"action_id",repr(action)),outcome.success))
            if not outcome.success:
                return {"success":False,"state":current,"events":tuple(events)}
            current=outcome.state
        return {"success":True,"state":current,"events":tuple(events)}
