class BranchPruner:
    def accept(self,depth,limit=None):
        return limit is None or depth <= limit
