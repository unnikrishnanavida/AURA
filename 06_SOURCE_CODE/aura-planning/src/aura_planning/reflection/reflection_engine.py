from .criticism.plan_critic import PlanCritic
class ReflectionEngine:
    def __init__(self): self.critic=PlanCritic()
    def critique(self,plan,constraints=None): return self.critic.critique(plan,constraints)
    def improve(self,plan,alternatives,score):
        return max((plan,)+tuple(alternatives),key=score,default=plan)
