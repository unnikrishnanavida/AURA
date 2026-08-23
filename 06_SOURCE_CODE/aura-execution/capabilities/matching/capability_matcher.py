def matches(requirement, capability):
    return capability is not None and capability.name==requirement.name and capability.supports(requirement.operation)
