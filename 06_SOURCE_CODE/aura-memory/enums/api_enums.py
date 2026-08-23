AURA Memory enums API adapter for api_enums.

from __future__ import annotations
import logging
from typing import Any, Callable, Dict

logger = logging.getLogger(__name__)


class ApiEnumsAPI:
    '''API adapter for enums.api_enums.'''

    def __init__(self) -> None:
        self._routes: Dict[str, Callable[[Dict[str, Any]], Dict[str, Any]]] = {}

    def register_route(self, path: str, handler: Callable[[Dict[str, Any]], Dict[str, Any]]) -> None:
        '''Register an API route.'''
        if not path.startswith('/'):
            raise ValueError("path must start with '/'")
        self._routes[path] = handler
        logger.debug("Registered route %s", path)

    def dispatch(self, path: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        '''Dispatch a request to the registered handler.'''
        handler = self._routes.get(path)
        if handler is None:
            raise ValueError(f"Route not found: {path}")
        return handler(payload)

    async def dispatch_async(self, path: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        '''Async dispatch wrapper.'''
        return self.dispatch(path, payload)


__all__ = ["ApiEnumsAPI"]
