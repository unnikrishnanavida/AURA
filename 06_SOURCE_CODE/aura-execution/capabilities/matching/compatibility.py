def compatibility(required, available):
    if required.name != available.name: return 0.0
    if required.operation in available.operations or "*" in available.operations: return 1.0
    return 0.0
