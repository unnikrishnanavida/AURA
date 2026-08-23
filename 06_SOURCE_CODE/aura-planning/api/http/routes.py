from ..schemas.api_request import ApiRequest
class RouteTable:
    def __init__(self): self._routes={}
    def add(self, method, path, handler):
        key=(method.upper(),path)
        if key in self._routes: raise ValueError(f"route already exists: {key}")
        self._routes[key]=handler
    def resolve(self, method, path): return self._routes.get((method.upper(),path))
    def dispatch(self, method, path, payload=None):
        handler=self.resolve(method,path)
        if handler is None: raise KeyError(f"route not found: {method} {path}")
        return handler(ApiRequest(path,payload or {}))
