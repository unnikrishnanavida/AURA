class ReplanningRoutes:
    def register(self, routes, handler):
        routes.add("POST","/plans/replan",handler.replan)
        return routes
