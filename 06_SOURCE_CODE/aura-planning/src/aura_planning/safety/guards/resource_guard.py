class ResourceGuard:
    def allow(self, requirements, resource_engine):
        return resource_engine.feasible(requirements)
