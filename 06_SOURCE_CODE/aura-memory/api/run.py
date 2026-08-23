"""Run a small WSGI server for the aura-memory API."""

from __future__ import annotations

import os
from wsgiref.simple_server import make_server
from typing import Tuple

from . import app


def run(host: str = "127.0.0.1", port: int = 8000) -> Tuple[str, int]:
    print(f"Starting aura-memory API on {host}:{port}")
    with make_server(host, port, app) as srv:
        try:
            srv.serve_forever()
        except KeyboardInterrupt:
            print("Shutting down")
    return (host, port)


if __name__ == "__main__":
    run()
