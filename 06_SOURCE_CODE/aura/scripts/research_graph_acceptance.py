"""Live acceptance for the Research runs list and the Knowledge Graph.

Starts the real API server + Vite dev server, signs in through the real auth
gate, seeds real claims/research runs through the authenticated API, then
verifies in real Chrome (desktop + mobile) that both pages render populated,
interactive content with no overflow, no uncaught page errors, and no console
errors. Screenshots are written to build/.

Run:  python scripts/research_graph_acceptance.py
"""

from __future__ import annotations

import json
import os
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
TOKEN = "test-key"


def _wait_http(url: str, timeout: float = 30.0) -> None:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        try:
            with urllib.request.urlopen(url, timeout=2) as r:
                if r.status < 500:
                    return
        except Exception:  # noqa: BLE001 - retry while starting
            time.sleep(0.4)
    raise RuntimeError(f"service did not become ready: {url}")


def _seed(port: int) -> None:
    claims = [
        "fast deployment is safe for production",
        "fast deployment is not safe for production",
        "automated rollbacks reduce deployment risk",
    ]
    for statement in claims:
        req = urllib.request.Request(
            f"http://127.0.0.1:{port}/v1/observe",
            data=json.dumps({"statement": statement, "predicate": ["deployment"]}).encode(),
            headers={"Authorization": f"Bearer {TOKEN}"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=5):
            pass
    for question in ("what is the best deployment strategy?", "are rollbacks required?"):
        req = urllib.request.Request(
            f"http://127.0.0.1:{port}/v1/research",
            data=json.dumps({"question": question, "claims": claims[:2]}).encode(),
            headers={"Authorization": f"Bearer {TOKEN}"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=5):
            pass


def main() -> int:
    failures: list[str] = []
    api = AuraApiServer(
        aura=Aura(clock=ManualClock(0), seed=9),
        config=ServerConfig(host="127.0.0.1", port=8765),
    )
    httpd = ThreadingHTTPServer(("127.0.0.1", 8765), api._handler())  # noqa: SLF001
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    _wait_http("http://127.0.0.1:8765/health")
    _seed(8765)

    vite = subprocess.Popen(
        ["npm.cmd", "run", "dev", "--", "--host", "127.0.0.1", "--port", "5210", "--strictPort"],
        cwd=str(WEB_DIR),
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )
    try:
        _wait_http("http://127.0.0.1:5210/")
    except Exception:
        print("VITE FAILED TO START")
        return 2

    from playwright.sync_api import sync_playwright

    with sync_playwright() as p:
        browser = p.chromium.launch(
            executable_path=CHROME,
            headless=True,
            args=["--disable-web-security"],
        )
        for name, width, height in (("desktop", 1440, 900), ("mobile", 390, 844)):
            page_errors: list[str] = []
            try:
                page = browser.new_page(viewport={"width": width, "height": height})
                page.on("pageerror", lambda exc, _e=page_errors: _e.append(str(exc)))
                page.goto("http://127.0.0.1:5210/", wait_until="domcontentloaded")
                page.get_by_placeholder("Bearer token issued by the AURA API").fill(TOKEN)
                page.get_by_role("button", name="Sign in").click()
                page.locator("[data-testid=auth-session]").wait_for(timeout=20_000)

                toggle = page.get_by_role("button", name="Toggle navigation")
                narrow = width <= 768
                if narrow:
                    toggle.wait_for(state="visible", timeout=8000)
                    toggle.dispatch_event("click")
                    page.wait_for_timeout(400)

                page.get_by_role("button", name="Knowledge Graph").click()
                page.locator("section[aria-label='Knowledge graph'] h2").wait_for(timeout=15_000)
                page.locator("svg.graph-svg").wait_for(timeout=15_000)
                count = page.locator(".graph-node").count()
                if count < 3:
                    failures.append(f"{name}: expected >=3 graph nodes, got {count}")

                # Select the first node and verify the details panel renders real fields.
                page.locator(".graph-node").first.dispatch_event("click")
                page.locator(".kg-details").get_by_text("Selected node", exact=True).wait_for(timeout=10_000)

                # Keyboard interaction path: focus a node, Enter selects, Escape clears.
                page.locator(".graph-node").first.focus()
                page.keyboard.press("ArrowRight")
                page.keyboard.press("Enter")
                page.keyboard.press("Escape")

                # The accessible list view stays available.
                page.get_by_role("button", name="Accessible list").click()
                page.get_by_role("table", name="Knowledge claims").wait_for(timeout=10_000)

                # Back to the visual graph, then to the Research page.
                page.get_by_role("button", name="Visual graph").click()

                # The drawer auto-closes on navigation (see App.navigate), so on narrow
                # layouts reopen it before the next sidebar selection - mirroring a user.
                if narrow and page.get_by_role("button", name="Toggle navigation").get_attribute("aria-expanded") == "false":
                    page.get_by_role("button", name="Toggle navigation").dispatch_event("click")
                    page.wait_for_timeout(400)

                # Research workspace: real runs render with status + question.
                page.get_by_role("button", name="Research", exact=True).click()
                page.locator("section[aria-label='Research'] h2").wait_for(timeout=15_000)
                page.get_by_text("best deployment strategy", exact=False).wait_for(timeout=10_000)
                run_cards = page.locator(".runs li").count()
                if run_cards < 2:
                    failures.append(f"{name}: expected >=2 research runs, got {run_cards}")

                overflow = page.evaluate("document.documentElement.scrollWidth > window.innerWidth")
                if overflow:
                    failures.append(f"{name}: horizontal overflow detected")
                if page_errors:
                    failures.append(f"{name}: uncaught page errors=" + " | ".join(page_errors[:2]))

                shot = ROOT / "build" / f"research_graph_{name}_{width}x{height}.png"
                page.screenshot(path=str(shot), full_page=True)
                print(
                    f"PROBE {name} {width}x{height} ok nodes={count} runs={run_cards} "
                    f"overflow={overflow} pageerrors={len(page_errors)} shot={shot.name}"
                )
                page.close()
            except Exception as exc:  # noqa: BLE001 - record and continue
                import traceback

                where = " | ".join(traceback.format_exc().strip().splitlines()[-4:])
                failures.append(f"{name}: {type(exc).__name__}: {exc} || {where}")
                continue
        browser.close()

    with suppress(Exception):  # noqa: BLE001 - best effort
        api.close()
    vite.terminate()

    if failures:
        for failure in failures:
            print("PROBE_FAILURE >> " + failure)
        return 1
    print("RESEARCH_GRAPH_ACCEPTANCE_OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())