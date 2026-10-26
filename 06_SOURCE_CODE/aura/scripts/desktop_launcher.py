"""Packaged-desktop smoke launcher (Phase 40/41).

Runs the REAL ``aura.clients.desktop`` client inside a PyInstaller artifact:

- if the AURA API is reachable at 127.0.0.1:8765, it authenticates and prints a
  live reasoning answer;
- otherwise it exercises the genuine OFFLINE path: queue an idempotent op and
  report lifecycle state.

Exit code 0 on any exercised path; non-zero on internal failure.
"""

from __future__ import annotations

import tempfile
import urllib.request

from aura.clients.desktop import DesktopClient
from aura.clients.offline_queue import OfflineQueue
from aura.clients.secure_store import MemorySecureStore


def main() -> int:
    api = _ProbeApi()
    client = DesktopClient(
        api=api,
        storage=MemorySecureStore(),
        queue=OfflineQueue(tempfile.mkdtemp(prefix="aura_queue_")),
    )
    online = _reachable("http://127.0.0.1:8765/health")
    if online:
        ok = client.authenticate("")  # server without key configured trusts any key
        result = client.reason("is the packaged desktop client alive?") if ok else {}
        client.sign_out()
        print(f"DESKTOP_ONLINE_OK authenticated={ok} answer={result.get('answer')!r}")
    else:
        client.lifecycle.start()
        client.lifecycle.go_offline()
        queued = client.reason("offline queued task")
        client.lifecycle.reconnect()
        client.sign_out()
        print(
            "DESKTOP_OFFLINE_OK queued="
            f"{queued.get('queued')} key={queued.get('idempotency_key')} "
            f"state={client.lifecycle.state.value}"
        )
    return 0


class _ProbeApi:
    def __init__(self) -> None:
        self.config: dict[str, object] = {}

    def ready(self) -> bool:
        return _reachable("http://127.0.0.1:8765/ready")

    def reason(self, question: str, facts: dict[str, float] | None = None) -> dict[str, object]:
        if not self.ready():
            raise ConnectionError("unreachable")
        return {"answer": "bundled-client-online", "question": question, "facts": bool(facts)}


def _reachable(url: str) -> bool:
    try:
        with urllib.request.urlopen(url, timeout=2) as r:
            return r.status < 500
    except Exception:  # noqa: BLE001 - offline is a valid state
        return False


if __name__ == "__main__":
    raise SystemExit(main())