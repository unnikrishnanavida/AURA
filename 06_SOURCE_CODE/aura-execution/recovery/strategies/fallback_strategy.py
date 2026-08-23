class FallbackStrategy:
    def choose(self,failure,fallback_available):return fallback_available and not failure.policy
