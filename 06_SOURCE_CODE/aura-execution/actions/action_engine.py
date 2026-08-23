from .dispatch.action_dispatcher import ActionDispatcher
class ActionEngine:
    def __init__(self,dispatcher=None):self.dispatcher=dispatcher or ActionDispatcher()
    def execute(self,action,inputs,context):
        return self.dispatcher.dispatch(action,inputs,context)
