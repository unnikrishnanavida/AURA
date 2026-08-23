class ResourcePolicy:
    def allows(self, resource, scopes):
        return resource in scopes or "*" in scopes
