def test_resource_allocation():
    from aura_planning.resources.models.resource import Resource
    from aura_planning.resources.models.resource_requirement import ResourceRequirement
    from aura_planning.resources.registry.resource_registry import ResourceRegistry
    from aura_planning.resources.allocation.resource_allocator import ResourceAllocator
    registry=ResourceRegistry([Resource("cpu",4)])
    assert ResourceAllocator().allocate([ResourceRequirement("cpu",2)],registry)=={"cpu":2}
