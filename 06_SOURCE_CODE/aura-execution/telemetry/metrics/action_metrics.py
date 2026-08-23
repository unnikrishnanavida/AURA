class ActionMetrics:
    def __init__(self):self.by_action={}
    def record(self,action_id,success):self.by_action.setdefault(action_id,[0,0]);self.by_action[action_id][0]+=1;self.by_action[action_id][1]+=int(success)
