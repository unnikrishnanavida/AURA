class HealthMonitor:
    def check(self,components):return {name:bool(value) for name,value in components.items()}
