from .validation.action_validator import ActionValidator
class ActionManager:
    def __init__(self, actions=()):
        self._actions={}
        self.validator=ActionValidator()
        for action in actions: self.register(action)

    def register(self, action):
        errors=self.validator.validate(action)
        if errors: raise ValueError("; ".join(errors))
        if action.action_id in self._actions: raise ValueError(f"duplicate action: {action.action_id}")
        self._actions[action.action_id]=action

    def get(self, action_id): return self._actions[action_id]
    def all(self): return tuple(self._actions.values())
    def applicable(self,state): return tuple(a for a in self._actions.values() if a.is_applicable(state))
    def execute(self, action_id, state): return self.get(action_id).apply(state)
