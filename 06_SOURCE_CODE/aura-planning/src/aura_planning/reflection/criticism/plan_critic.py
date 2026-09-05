class PlanCritic:
    def critique(self,plan,constraints=None):
        findings=[]
        actions=tuple(getattr(plan,"actions",plan))
        if not actions: findings.append("plan has no actions")
        if constraints:
            findings.extend(constraints.validate(plan))
        for a in actions:
            if not getattr(a,"preconditions",()): findings.append(f"action lacks preconditions: {getattr(a,'name',a)}")
        return tuple(findings)
