class PlanMerger:
    def merge(self,plans):
        actions=[]; seen=set()
        for plan in plans:
            for action in getattr(plan,"actions",plan):
                key=getattr(action,"action_id",repr(action))
                if key not in seen: seen.add(key); actions.append(action)
        return tuple(actions)
