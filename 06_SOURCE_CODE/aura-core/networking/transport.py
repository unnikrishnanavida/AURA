from __future__ import annotations

from typing import Protocol

from .request import Request
from .response import Response


class Transport(Protocol):
    def send(self, request: Request) -> Response: ...
