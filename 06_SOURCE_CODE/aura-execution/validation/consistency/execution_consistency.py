def consistent(before,after,declared_effects):
    return all(after.get(k)==v for k,v in declared_effects.items())
