class ScenarioGenerator:
    def generate(self, baseline, perturbations):
        return tuple(p if hasattr(p,"state_updates") else baseline for p in perturbations)
