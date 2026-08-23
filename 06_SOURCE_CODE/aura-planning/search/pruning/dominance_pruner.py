class DominancePruner:
    def accept(self,cost,best_cost):
        return best_cost is None or cost < best_cost
