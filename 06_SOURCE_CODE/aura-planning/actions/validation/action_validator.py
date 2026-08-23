class ActionValidator:
    def validate(self, action):
        errors=[]
        if not action.action_id: errors.append("missing action_id")
        if not action.name: errors.append("missing name")
        if action.duration < 0: errors.append("negative duration")
        if action.cost < 0: errors.append("negative cost")
        if not 0 <= action.risk <= 1: errors.append("risk outside [0,1]")
        return tuple(errors)
