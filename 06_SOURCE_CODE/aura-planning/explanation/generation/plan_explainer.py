class PlanExplainer:
    def explain(self,plan):
        actions=tuple(getattr(plan,"actions",plan))
        lines=[f"Selected plan contains {len(actions)} actions."]
        for i,a in enumerate(actions,1):
            lines.append(
                f"{i}. {getattr(a,'name',getattr(a,'action_id',str(a)))} "
                f"(cost={getattr(a,'cost',0)}, duration={getattr(a,'duration',0)}, risk={getattr(a,'risk',0)})"
            )
        return "\n".join(lines)
