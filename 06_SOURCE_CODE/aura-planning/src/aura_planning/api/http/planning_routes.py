from .routes import RouteTable
class PlanningRoutes:
    def register(self, routes, handler):
        routes.add("POST","/plans",handler.plan)
        return routes
