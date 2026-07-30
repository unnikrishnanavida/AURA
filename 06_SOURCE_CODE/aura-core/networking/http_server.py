from __future__ import annotations

from http.server import HTTPServer, BaseHTTPRequestHandler
from typing import Callable


class SimpleHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"OK")


class HttpServer:
    def __init__(self, host: str = "127.0.0.1", port: int = 8000, handler: Callable | None = None) -> None:
        self.host = host
        self.port = port
        self._handler = handler or SimpleHandler
        self._server: HTTPServer | None = None

    def start(self):
        self._server = HTTPServer((self.host, self.port), self._handler)
        self._server.serve_forever()

    def stop(self):
        if self._server:
            self._server.shutdown()
