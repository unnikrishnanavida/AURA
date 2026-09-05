class CapacityPlanner:
    def feasible(self, requirements, capacity):
        return all(
            requirements.get(name, 0) <= capacity.get(name, 0)
            for name in requirements
        )

    def deficit(self, requirements, capacity):
        return {
            name: max(0, requirements.get(name, 0) - capacity.get(name, 0))
            for name in requirements
            if requirements.get(name, 0) > capacity.get(name, 0)
        }
