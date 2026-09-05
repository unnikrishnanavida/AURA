class SimulationRoutes:
    def register(self, routes, handler):
        routes.add("POST","/plans/simulate",handler.simulate)
        return routes
