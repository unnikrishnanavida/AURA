class WorldStateAdapter:
    def to_planning_state(self, observations):
        values={}
        for observation in observations:
            values.update({f"{observation.entity}.{k}":v for k,v in observation.values.items()})
        return values
