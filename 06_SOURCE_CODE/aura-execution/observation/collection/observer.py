from ..models.observation import Observation
class Observer:
    def observe(self,before,after):
        changes={k:(before.get(k),after.get(k)) for k in set(before)|set(after) if before.get(k)!=after.get(k)}
        return Observation(before,after,changes,False)
