class PlanSimulator:
    def simulate(self,plan,state):
        current=state
        history=[]
        for action in getattr(plan,"actions",plan):
            outcome=action.apply(current); history.append(outcome)
            if not outcome.success:
                return {"success":False,"state":current,"history":tuple(history),"failed_action":action}
            current=outcome.state
        return {"success":True,"state":current,"history":tuple(history)}
