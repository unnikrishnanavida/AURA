def is_permanent(failure):return not failure.transient and not failure.policy and not failure.resource
