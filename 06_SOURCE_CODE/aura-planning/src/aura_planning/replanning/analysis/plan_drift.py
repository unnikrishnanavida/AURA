class PlanDrift:
    def affected_suffix(self,planned_actions,observed_state,action_checker):
        for index,action in enumerate(planned_actions):
            if not action_checker(action,observed_state):
                return tuple(planned_actions[index:]), index
        return (), len(planned_actions)
