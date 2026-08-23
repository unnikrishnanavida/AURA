import importlib.util
import json
import os
import threading
import urllib.error
import urllib.request
from wsgiref.simple_server import make_server

# Load api module directly from path
_here = os.path.dirname(__file__)
_api_init = os.path.join(_here, "__init__.py")
spec = importlib.util.spec_from_file_location("aura_memory.api", _api_init)
api = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(api)


def main():
    with make_server("127.0.0.1", 8001, api.app) as srv:
        thread = threading.Thread(target=srv.serve_forever, daemon=True)
        thread.start()

        base = "http://127.0.0.1:8001"
        with urllib.request.urlopen(base + "/health") as resp:
            assert resp.status == 200
            body = json.loads(resp.read().decode("utf-8"))
            assert body["status"] == "ok"

        try:
            urllib.request.urlopen(base + "/get?key=test")
            assert False, "Expected unauthorized"
        except urllib.error.HTTPError as exc:
            assert exc.code == 401

        # metrics endpoint should work without auth
        with urllib.request.urlopen(base + "/metrics") as resp:
            assert resp.status == 200
            body = json.loads(resp.read().decode("utf-8"))
            assert "counters" in body and "gauges" in body

        srv.shutdown()
        thread.join(timeout=2.0)

    print("API smoke test passed")


if __name__ == "__main__":
    main()
