from __future__ import annotations

import urllib.request
import urllib.error
from typing import Dict, Any

from .request import Request
from .response import Response


class HttpClient:
    def send(self, req: Request, timeout: int = 30) -> Response:
        r = urllib.request.Request(req.url, data=(req.body or None), method=req.method)
        for k, v in (req.headers or {}).items():
            r.add_header(k, v)
        try:
            with urllib.request.urlopen(r, timeout=timeout) as fh:
                body = fh.read()
                headers = dict(fh.getheaders())
                return Response(status_code=fh.getcode(), headers=headers, body=body)
        except urllib.error.HTTPError as exc:
            return Response(status_code=exc.code, headers=dict(exc.headers), body=exc.read())
