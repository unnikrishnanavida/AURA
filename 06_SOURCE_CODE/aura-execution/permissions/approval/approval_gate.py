class ApprovalGate:
    def __init__(self, manager): self.manager=manager
    def check(self,action_id,required): return (not required) or self.manager.is_approved(action_id)
