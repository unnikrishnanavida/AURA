class FallbackValidator:
    def validate(self, fallback, constraints=None):
        if fallback is None: return ["fallback is missing"]
        if not fallback.acceptable(): return ["fallback exceeds risk threshold"]
        return list(constraints.validate(fallback.plan)) if constraints else []
