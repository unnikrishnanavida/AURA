class PermissionPolicy:
    def __init__(self, rules=None): self.rules=rules or {}
    def decide(self, principal, permission):
        return self.rules.get((principal,permission),"deny")
