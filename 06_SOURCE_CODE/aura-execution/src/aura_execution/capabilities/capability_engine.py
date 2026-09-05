from .matching.capability_matcher import matches
from .models.capability_requirement import CapabilityRequirement


class CapabilityEngine:
    def __init__(self,registry): self.registry=registry
    def check(self,name,operation):
        cap=self.registry.get(name)
        return matches(CapabilityRequirement(name,operation),cap)
