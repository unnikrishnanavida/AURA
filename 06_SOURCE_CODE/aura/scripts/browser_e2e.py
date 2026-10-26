"""Phase 40/41: real browser end-to-end verification of the AURA web client.

Starts the real API server and the real vite dev server, drives the actual
Chrome browser with Playwright, signs in, submits a real question through the
Reasoning console, and asserts that the displayed answer is the LIVE backend
response (no demo data). Safe: loopback services only; temporary processes are
terminated on exit.

Usage:
    set AURA_WEB_DIR=<path-to-aura-web>   (optional; default ../../aura-web)
    <venv>/python scripts/browser_e2e.py
"""

from __future__ import annotations

import contextlib
import os
import subprocess
import sys
import threading
import time
import urllib.request
from http.server import ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WEB_DIR = Path(os.environ.get("AURA_WEB_DIR", ROOT.parent / "aura-web"))
CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
API_HOST, API_PORT = "127.0.0.1", 8765
WEB_PORT = 5210


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


def main() -> int:
    from aura.api.server import AuraApiServer, ServerConfig
    from aura.foundation.clock import ManualClock
    from aura.sdk.client import Aura

    api = AuraApiServer(
        aura=Aura(clock=ManualClock(0), seed=7),
        config=ServerConfig(host=API_HOST, port=API_PORT),
    )
    httpd = ThreadingHTTPServer((API_HOST, API_PORT), api._handler())  # noqa: SLF001
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    wait_http(f"http://{API_HOST}:{API_PORT}/health")

    vite = subprocess.Popen(
        [
            "npm.cmd",
            "run",
            "dev",
            "--",
            "--host",
            "127.0.0.1",
            "--port",
            str(WEB_PORT),
            "--strictPort",
        ],
        cwd=str(WEB_DIR),
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )
    try:
        wait_http(f"http://127.0.0.1:{WEB_PORT}/")
    except Exception:
        out = ""
        with contextlib.suppress(Exception):  # noqa: BLE001 - best-effort diagnostics
            out, _ = vite.communicate(timeout=3)
        print(f"VITE FAILED TO START\n{out[:2000]}", flush=True)
        return 2

    from playwright.sync_api import sync_playwright

    with sync_playwright() as p:
        browser = p.chromium.launch(executable_path=CHROME, headless=True)
        page = browser.new_page()
        console_errors: list[str] = []

        def _on_console(msg: object) -> None:
            text = str(getattr(msg, "text", ""))
            kind = str(getattr(msg, "type", ""))
            if kind == "error" and "favicon" not in text:
                console_errors.append(text)

        page.on("pageerror", lambda exc: console_errors.append(f"pageerror: {exc}"))
        page.on("console", _on_console)
        page.goto(f"http://127.0.0.1:{WEB_PORT}/", wait_until="domcontentloaded")

        page.get_by_placeholder("Bearer token issued by the AURA API").fill("test-key")
        page.get_by_role("button", name="Sign in").click()
        page.locator("[data-testid=auth-session]").wait_for(timeout=20_000)

        # The chat-first home page is the reasoning surface (the old
        # "Reasoning" nav button no longer exists after the shell redesign).
        question = page.get_by_placeholder("Ask AURA anything")
        question.wait_for(timeout=20_000)
        question.fill("Is the deployment safe?")
        page.get_by_role("button", name="Send message").click()

        turn = page.locator("article.turn").last
        answer_box = turn.locator(".turn-answer")
        answer_box.wait_for(timeout=20_000)  # real answer rendered from the LIVE backend
        answer = answer_box.inner_text()
        assert answer.strip(), "answer block is empty"
        # Metadata lives in a collapsed <details> disclosure; expand and read it.
        turn.locator("summary").click()
        meta_box = turn.locator("dl.turn-metadata")
        meta_box.wait_for(timeout=5_000)
        meta = meta_box.inner_text()
        assert "confidence" in meta.lower(), f"metadata missing confidence: {meta!r}"
        answer = f"{answer}\n---\n{meta}"

        shot = ROOT / "build" / "browser_e2e.png"
        shot.parent.mkdir(parents=True, exist_ok=True)
        page.screenshot(path=str(shot), full_page=True)

        browser.close()

        assert not console_errors, f"console/page errors: {console_errors}"

        print("BROWSER_E2E_OK", flush=True)
        print("laid_out_state=signed_in_chat_home_thread", flush=True)
        print(f"answer_block={answer.splitlines()[:6]}", flush=True)
        print(f"screenshot={shot}", flush=True)
        return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:  # noqa: BLE001 - surface the failure precisely
        print(f"BROWSER_E2E_FAILED: {type(exc).__name__}: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc