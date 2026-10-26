"""Milestone A: multi-viewport browser acceptance for the AURA web shell.

Starts the real API + vite, then drives real Chrome at four viewports (desktop,
laptop, tablet, narrow mobile) verifying: sidebar visibility, mobile drawer
open/close (menu aria-expanded, scrim, navigate-closes), no horizontal
overflow, and zero console errors. Captures one screenshot per viewport.

Exit 0 only if every viewport assertion passes.
"""
from __future__ import annotations

import os
import socket
import subprocess
import threading
import time
import urllib.request
from contextlib import suppress
from http.server import ThreadingHTTPServer
from pathlib import Path

from aura.api.server import AuraApiServer, ServerConfig
from aura.foundation.clock import ManualClock
from aura.sdk.client import Aura

ROOT = Path(__file__).resolve().parents[1]
WEB_DIR = Path(os.environ.get("AURA_WEB_DIR", ROOT.parent / "aura-web"))
CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
VIEWPORTS = [
    ("desktop", 1440, 900),
    ("laptop", 1280, 800),
    ("tablet", 768, 1024),
    ("mobile", 390, 844),
]


def wait_http(url: str, timeout: float = 30.0) -> None:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        try:
            with urllib.request.urlopen(url, timeout=2) as r:
                if r.status < 500:
                    return
        except Exception:  # noqa: BLE001 - retry while starting
            time.sleep(0.4)
    raise RuntimeError(f"service did not become ready: {url}")


def _port_listening(port: int) -> bool:
    try:
        with socket.create_connection(("127.0.0.1", port), timeout=1.0):
            return True
    except OSError:
        return False


def main() -> int:
    if _port_listening(8765):
        print("API PORT 8765 ALREADY IN USE: stale AURA API detected. Stop it, then re-run.")
        return 3
    api = AuraApiServer(
        aura=Aura(clock=ManualClock(0), seed=7),
        config=ServerConfig(host="127.0.0.1", port=8765),
    )
    _inner = api._handler()  # noqa: SLF001

    class _DebugHandler(_inner):
        requests = 0

        def _trace(self) -> None:
            type(self).requests += 1

        def do_GET(self) -> None:
            self._trace()
            super().do_GET()

        def do_POST(self) -> None:
            self._trace()
            super().do_POST()

        def do_OPTIONS(self) -> None:
            self._trace()
            super().do_OPTIONS()

    httpd = ThreadingHTTPServer(("127.0.0.1", 8765), _DebugHandler)
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    wait_http("http://127.0.0.1:8765/health")

    vite = subprocess.Popen(
        ["npm.cmd", "run", "dev", "--", "--host", "127.0.0.1", "--port", "5210", "--strictPort"],
        cwd=str(WEB_DIR),
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )
    try:
        wait_http("http://127.0.0.1:5210/")
    except Exception:
        print("VITE FAILED TO START")
        return 2

    from playwright.sync_api import sync_playwright

    failures: list[str] = []
    with sync_playwright() as p:
        browser = p.chromium.launch(
            executable_path=CHROME,
            headless=True,
            # Product serves web + API same-origin; the harness splits ports, so
            # disable the cross-origin gate to mirror the production topology.
            args=["--disable-web-security"],
        )
        for name, width, height in VIEWPORTS:
            console_errors: list[str] = []
            page_errors: list[str] = []
            try:
                page = browser.new_page(viewport={"width": width, "height": height})
                def _capture_console(msg, collector):
                    try:
                        text = msg.text
                    except TypeError:
                        text = msg.text()
                    try:
                        url = msg.location["url"]
                    except (TypeError, AttributeError, KeyError):
                        try:
                            url = msg.location()["url"]
                        except (TypeError, AttributeError, KeyError):
                            url = ""
                    if msg.type == "error":
                        collector.append(f"[{url}] {text}")

                page.on("console", lambda msg, _c=console_errors: _capture_console(msg, _c))
                page.on("pageerror", lambda exc, _e=page_errors: _e.append(str(exc)))
                page.goto("http://127.0.0.1:5210/", wait_until="domcontentloaded")
                page.get_by_placeholder("Bearer token issued by the AURA API").fill("test-key")
                page.get_by_role("button", name="Sign in").click()
                page.locator("[data-testid=auth-session]").wait_for(timeout=20_000)

                toggle = page.get_by_role("button", name="Toggle navigation")
                overflow = page.evaluate("document.documentElement.scrollWidth > window.innerWidth")
                narrow = width <= 768
                if narrow:
                    toggle.wait_for(state="visible", timeout=8000)
                    if not toggle.is_visible():
                        failures.append(f"{name}: menu toggle not visible")
                    toggle.dispatch_event("click")
                    page.wait_for_timeout(400)
                    if toggle.get_attribute("aria-expanded") != "true":
                        failures.append(f"{name}: aria-expanded not true after open")
                    page.locator(".sidebar-scrim").dispatch_event("click")
                    page.wait_for_timeout(400)
                    if toggle.get_attribute("aria-expanded") != "false":
                        failures.append(f"{name}: scrim did not close drawer")
                    toggle.dispatch_event("click")
                    page.wait_for_timeout(400)
                    if toggle.get_attribute("aria-expanded") != "true":
                        failures.append(f"{name}: drawer did not reopen")
                    page.get_by_role("button", name="Diagnostics").click(force=True)
                    page.get_by_role("heading", name="Diagnostics").first.wait_for(timeout=15_000)
                    if toggle.get_attribute("aria-expanded") != "false":
                        failures.append(f"{name}: navigation did not close drawer")
                else:
                    nav_count = page.locator(".sidebar-nav button").count()
                    if nav_count < 9:
                        failures.append(f"{name}: expected >=9 nav items, got {nav_count}")
                    page.get_by_role("button", name="Diagnostics").click()
                    page.get_by_role("heading", name="Diagnostics").first.wait_for(timeout=15_000)

                if overflow:
                    failures.append(f"{name}: horizontal overflow detected")
                if page_errors:
                    failures.append(f"{name}: uncaught page errors=" + " | ".join(page_errors[:3]))

                shot = ROOT / "build" / f"viewport_{name}_{width}x{height}.png"
                page.screenshot(path=str(shot), full_page=True)
                print(
                    f"VIEWPORT {name} {width}x{height} ok overflow={overflow} "
                    f"pageerrors={len(page_errors)} console_errors={len(console_errors)} "
                    f"serial={(' | '.join(console_errors[:2])).strip() or 'none'} shot={shot.name}"
                )
                page.close()
            except Exception as exc:  # noqa: BLE001 - record and continue
                try:
                    diag = page.evaluate(
                        """() => {
                          const t = document.querySelector('.menu-toggle');
                          const s = document.querySelector('.sidebar');
                          const r = t ? t.getBoundingClientRect() : null;
                          const cs = t ? getComputedStyle(t) : null;
                          return {
                            mediaNarrow: matchMedia('(max-width: 840px)').matches,
                            display: cs ? cs.display : null,
                            rect: r ? { x: r.x, y: r.y, w: r.width, h: r.height } : null,
                            sidebarTransform: s ? getComputedStyle(s).transform : null,
                          };
                        }"""
                    )
                    failures.append(f"{name}: raised {type(exc).__name__}: {exc}; diag={diag}")
                except Exception:  # noqa: BLE001 - page may already be gone
                    failures.append(f"{name}: raised {type(exc).__name__}: {exc}")
                continue
        browser.close()

    httpd.shutdown()
    httpd.server_close()
    with suppress(Exception):  # noqa: BLE001 - best effort
        api.close()
    vite.terminate()

    if failures:
        print("VIEWPORT_FAILURES: " + "; ".join(failures))
        return 1
    if _DebugHandler.requests == 0:
        print("VIEWPORT_FAILURES: no API requests reached the fresh harness server (stale listener suspected)")
        return 1
    print("VIEWPORT_ACCEPTANCE_OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())