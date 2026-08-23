from .scheduling.parallel_scheduler import parallel_groups
class ConcurrencyEngine:
    def groups(self,dependencies):return parallel_groups(dependencies)
