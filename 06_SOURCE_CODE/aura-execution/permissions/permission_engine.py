class PermissionEngine:
    def __init__(self, policy, resources, approvals):
        self.policy,self.resources,self.approvals=policy,resources,approvals
    def authorize(self, principal, action, context):
        if action.action_id in getattr(context,"approved_actions",set()): return "allow"
        for permission in action.permissions:
            if self.policy.decide(principal,permission) != "allow": return "deny"
        if action.capability and not self.resources.allows(action.capability,context.scopes):
            return "deny"
        if action.risk >= 0.75 and not context.approved: return "review"
        return "allow"
