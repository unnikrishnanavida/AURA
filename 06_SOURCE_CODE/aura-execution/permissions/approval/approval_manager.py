class ApprovalManager:
    def __init__(self): self._approved=set()
    def approve(self,action_id): self._approved.add(action_id)
    def revoke(self,action_id): self._approved.discard(action_id)
    def is_approved(self,action_id): return action_id in self._approved
