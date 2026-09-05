class CapacityProfile:
    def __init__(self, capacities):
        self.capacities = dict(capacities)
    def available(self, name): return self.capacities.get(name, 0)
    def consume(self, name, amount):
        if self.available(name) < amount:
            raise ValueError(f"insufficient capacity for {name}")
        self.capacities[name] -= amount
