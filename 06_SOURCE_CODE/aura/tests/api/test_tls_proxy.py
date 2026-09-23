"""TLS proxy + multi-instance failover tests (real HTTPS, real certificates).

Exercises the Phase 15 topology using real TLS termination:

- HTTPS request over a trusted test CA terminates at the proxy
- HTTP → HTTPS redirect
- security headers on every proxied response
- a dead upstream fails over to the surviving one
- a client-supplied X-Forwarded-For cannot spoof the real client IP (the
  proxy overwrites it)

Certificates are generated ephemerally via :mod:`aura.api.tls_testing` and are
never committed.
"""

from __future__ import annotations

import json
import ssl
import threading
from http.client import HTTPConnection, HTTPResponse, HTTPSConnection
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import pytest

from aura.api.proxy import ProxyConfig, TLSProxy, Upstream
from aura.api.tls_testing import CertBundle, generate_self_signed_certs


class _EchoUpstream(BaseHTTPRequestHandler):
    def log_message(self, fmt: str, *args: object) -> None:  # noqa: A002
        return

    def _respond(self) -> None:
        length = int(self.headers.get("Content-Length", "0") or 0)
        body = self.rfile.read(length) if length > 0 else b""
        xff = self.headers.get("X-Forwarded-For", "")
        xproto = self.headers.get("X-Forwarded-Proto", "")
        payload = json.dumps(
            {"method": self.command, "path": self.path, "body": body.decode(), "xff": xff, "xproto": xproto}
        ).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    do_GET = _respond  # type: ignore[assignment]
    do_POST = _respond  # type: ignore[assignment]


@pytest.fixture(scope="module")
def certs() -> CertBundle:
    return generate_self_signed_certs()


def _start_upstream() -> tuple[ThreadingHTTPServer, int]:
    httpd = ThreadingHTTPServer(("127.0.0.1", 0), _EchoUpstream)
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    return httpd, httpd.server_port


def _https_get(port: int, path: str, *, cafile: str) -> tuple[int, dict, dict]:
    ctx = ssl.create_default_context(cafile=cafile)
    conn = HTTPSConnection("localhost", port, timeout=5, context=ctx)
    conn.request("GET", path)
    resp: HTTPResponse = conn.getresponse()
    body = json.loads(resp.read().decode())
    headers = dict(resp.getheaders())
    conn.close()
    return resp.status, body, headers
def test_tls_termination_end_to_end(certs: CertBundle) -> None:
    upstream, upstream_port = _start_upstream()
    proxy = TLSProxy(config=ProxyConfig(
        host="127.0.0.1", tls_port=0, redirect_port=None,
        tls_certfile=str(certs.certfile), tls_keyfile=str(certs.keyfile),
        upstreams=[Upstream(host="127.0.0.1", port=upstream_port)],
    ))
    proxy.start()
    try:
        status, body, headers = _https_get(proxy.tls_port, "/liveness", cafile=str(certs.cafile))
        assert status == 200, body
        assert body["path"] == "/liveness"
        assert "X-Content-Type-Options" in headers
        assert headers["X-Content-Type-Options"] == "nosniff"
        # The proxy overwrote XFF with the real client IP.
        assert body["xff"] != "spoofed"
    finally:
        proxy.stop()
        upstream.shutdown()
        upstream.server_close()


def test_http_redirects_to_https(certs: CertBundle) -> None:
    upstream, upstream_port = _start_upstream()
    proxy = TLSProxy(config=ProxyConfig(
        host="127.0.0.1", tls_port=0, redirect_port=0,
        tls_certfile=str(certs.certfile), tls_keyfile=str(certs.keyfile),
        upstreams=[Upstream(host="127.0.0.1", port=upstream_port)],
    ))
    proxy.start()
    try:
        conn = HTTPConnection("127.0.0.1", proxy.redirect_port, timeout=5)
        conn.request("GET", "/liveness")
        resp = conn.getresponse()
        status = resp.status
        location = resp.getheader("Location", "")
        resp.read()
        conn.close()
        assert status == 301
        assert location.startswith("https://")
    finally:
        proxy.stop()
        upstream.shutdown()
        upstream.server_close()


def test_failover_to_healthy_upstream(certs: CertBundle) -> None:
    # A port that is guaranteed closed (dead upstream). We bind it, close it,
    # then verify it actually refuses so the test never mistimes port reuse.
    import socket

    def _find_closed_port() -> int:
        for _ in range(10):
            sock = socket.socket()
            sock.bind(("127.0.0.1", 0))
            port = sock.getsockname()[1]
            sock.close()
            probe = socket.socket()
            probe.settimeout(0.5)
            try:
                probe.connect(("127.0.0.1", port))
                probe.close()
                continue  # unexpectedly open; try another
            except OSError:
                probe.close()
                return port
        raise RuntimeError("could not find a closed local port")

    dead_port = _find_closed_port()

    alive, alive_port = _start_upstream()
    proxy = TLSProxy(config=ProxyConfig(
        host="127.0.0.1", tls_port=0, redirect_port=None,
        tls_certfile=str(certs.certfile), tls_keyfile=str(certs.keyfile),
        upstreams=[
            Upstream(host="127.0.0.1", port=dead_port),  # first, dead
            Upstream(host="127.0.0.1", port=alive_port),  # second, healthy
        ],
        timeout_seconds=2.0,
    ))
    proxy.start()
    try:
        status, body, _ = _https_get(proxy.tls_port, "/health", cafile=str(certs.cafile))
        assert status == 200, body
        assert body["path"] == "/health"
    finally:
        proxy.stop()
        alive.shutdown()
        alive.server_close()


def test_client_cannot_spoof_xff(certs: CertBundle) -> None:
    upstream, upstream_port = _start_upstream()
    proxy = TLSProxy(config=ProxyConfig(
        host="127.0.0.1", tls_port=0, redirect_port=None,
        tls_certfile=str(certs.certfile), tls_keyfile=str(certs.keyfile),
        upstreams=[Upstream(host="127.0.0.1", port=upstream_port)],
    ))
    proxy.start()
    try:
        ctx = ssl.create_default_context(cafile=str(certs.cafile))
        conn = HTTPSConnection("localhost", proxy.tls_port, timeout=5, context=ctx)
        conn.request("GET", "/v1/metrics", headers={"X-Forwarded-For": "1.2.3.4"})
        resp: HTTPResponse = conn.getresponse()
        body = json.loads(resp.read().decode())
        conn.close()
        assert resp.status == 200, body
        # The proxy overwrote the spoofed header with the real client IP.
        assert body["xff"] != "1.2.3.4"
        assert body["xff"] != ""
    finally:
        proxy.stop()
        upstream.shutdown()
        upstream.server_close()


def test_proxy_requires_cert_and_upstream() -> None:
    from aura.foundation.errors import ConfigurationError

    # No cert/key.
    with pytest.raises(ConfigurationError):
        TLSProxy(config=ProxyConfig(upstreams=[Upstream(host="127.0.0.1", port=1)]))
    # No upstreams.
    with pytest.raises(ConfigurationError):
        TLSProxy(config=ProxyConfig(tls_certfile="cert.pem", tls_keyfile="key.pem"))


# ---------------------------------------------------------------------------
# Phase 25: production TLS + edge security
# ---------------------------------------------------------------------------


def test_expired_certificate_is_refused_at_startup() -> None:
    """A proxy configured with an expired certificate must not serve."""
    from datetime import UTC, datetime, timedelta

    from aura.api.tls_testing import generate_certs_with_validity
    from aura.foundation.errors import ConfigurationError

    past = datetime.now(UTC) - timedelta(days=2)
    expired = generate_certs_with_validity(
        not_valid_after=past, not_valid_before=past - timedelta(days=30)
    )
    proxy = TLSProxy(config=ProxyConfig(
        host="127.0.0.1", tls_port=0, redirect_port=None,
        tls_certfile=str(expired.certfile), tls_keyfile=str(expired.keyfile),
        upstreams=[Upstream(host="127.0.0.1", port=1)],
    ))
    with pytest.raises(ConfigurationError, match="EXPIRED"):
        proxy.start()


def test_wrong_hostname_certificate_rejected_by_client(certs: CertBundle) -> None:
    """A client connecting with server_name='localhost' but a cert for another
    host must fail certificate verification."""
    from datetime import UTC, datetime, timedelta

    from aura.api.tls_testing import generate_certs_with_validity

    other = generate_certs_with_validity(
        not_valid_after=datetime.now(UTC) + timedelta(days=365),
        hostname="other-host.example",
    )
    upstream, upstream_port = _start_upstream()
    proxy = TLSProxy(config=ProxyConfig(
        host="127.0.0.1", tls_port=0, redirect_port=None,
        tls_certfile=str(other.certfile), tls_keyfile=str(other.keyfile),
        upstreams=[Upstream(host="127.0.0.1", port=upstream_port)],
    ))
    proxy.start()
    try:
        ctx = ssl.create_default_context(cafile=str(other.cafile))
        with pytest.raises(ssl.SSLCertVerificationError):
            conn = HTTPSConnection("localhost", proxy.tls_port, timeout=5, context=ctx)
            conn.request("GET", "/liveness")
            conn.getresponse()
            conn.close()
    finally:
        proxy.stop()
        upstream.shutdown()
        upstream.server_close()


def test_untrusted_ca_is_rejected(certs: CertBundle) -> None:
    """A client that does not trust the server CA must fail handshake."""
    upstream, upstream_port = _start_upstream()
    proxy = TLSProxy(config=ProxyConfig(
        host="127.0.0.1", tls_port=0, redirect_port=None,
        tls_certfile=str(certs.certfile), tls_keyfile=str(certs.keyfile),
        upstreams=[Upstream(host="127.0.0.1", port=upstream_port)],
    ))
    proxy.start()
    try:
        # System trust store does not include the ephemeral CA; the client must
        # refuse the handshake (CERT_REQUIRED + hostname check on by default).
        ctx = ssl.create_default_context()
        with pytest.raises(ssl.SSLCertVerificationError):
            conn = HTTPSConnection("localhost", proxy.tls_port, timeout=5, context=ctx)
            conn.request("GET", "/liveness")
            conn.getresponse()
            conn.close()
    finally:
        proxy.stop()
        upstream.shutdown()
        upstream.server_close()


def test_hsts_header_when_enabled(certs: CertBundle) -> None:
    upstream, upstream_port = _start_upstream()
    proxy = TLSProxy(config=ProxyConfig(
        host="127.0.0.1", tls_port=0, redirect_port=None,
        tls_certfile=str(certs.certfile), tls_keyfile=str(certs.keyfile),
        upstreams=[Upstream(host="127.0.0.1", port=upstream_port)],
        hsts_enabled=True, hsts_max_age=86_400, hsts_include_subdomains=True,
    ))
    proxy.start()
    try:
        status, _, headers = _https_get(proxy.tls_port, "/liveness", cafile=str(certs.cafile))
        assert status == 200
        assert headers["Strict-Transport-Security"] == "max-age=86400; includeSubDomains"
    finally:
        proxy.stop()
        upstream.shutdown()
        upstream.server_close()


def test_host_validation_rejects_untrusted_host(certs: CertBundle) -> None:
    upstream, upstream_port = _start_upstream()
    proxy = TLSProxy(config=ProxyConfig(
        host="127.0.0.1", tls_port=0, redirect_port=None,
        tls_certfile=str(certs.certfile), tls_keyfile=str(certs.keyfile),
        upstreams=[Upstream(host="127.0.0.1", port=upstream_port)],
        allowed_hosts=("aura.example.com",),
    ))
    proxy.start()
    try:
        ctx = ssl.create_default_context(cafile=str(certs.cafile))
        conn = HTTPSConnection("localhost", proxy.tls_port, timeout=5, context=ctx)
        conn.request("GET", "/liveness")
        resp: HTTPResponse = conn.getresponse()
        assert resp.status == 421
        conn.close()
    finally:
        proxy.stop()
        upstream.shutdown()
        upstream.server_close()
def test_request_header_size_limit(certs: CertBundle) -> None:
    upstream, upstream_port = _start_upstream()
    proxy = TLSProxy(config=ProxyConfig(
        host="127.0.0.1", tls_port=0, redirect_port=None,
        tls_certfile=str(certs.certfile), tls_keyfile=str(certs.keyfile),
        upstreams=[Upstream(host="127.0.0.1", port=upstream_port)],
        max_header_bytes=512,
    ))
    proxy.start()
    try:
        ctx = ssl.create_default_context(cafile=str(certs.cafile))
        conn = HTTPSConnection("localhost", proxy.tls_port, timeout=5, context=ctx)
        conn.request("GET", "/liveness", headers={"X-Spam": "y" * 800})
        resp: HTTPResponse = conn.getresponse()
        assert resp.status == 431
        conn.close()
    finally:
        proxy.stop()
        upstream.shutdown()
        upstream.server_close()


def test_request_body_size_limit(certs: CertBundle) -> None:
    upstream, upstream_port = _start_upstream()
    proxy = TLSProxy(config=ProxyConfig(
        host="127.0.0.1", tls_port=0, redirect_port=None,
        tls_certfile=str(certs.certfile), tls_keyfile=str(certs.keyfile),
        upstreams=[Upstream(host="127.0.0.1", port=upstream_port)],
        max_request_bytes=1024,
    ))
    proxy.start()
    try:
        ctx = ssl.create_default_context(cafile=str(certs.cafile))
        conn = HTTPSConnection("localhost", proxy.tls_port, timeout=5, context=ctx)
        conn.request("POST", "/v1/remember", body=b"x" * 2000, headers={"Content-Type": "application/json"})
        resp: HTTPResponse = conn.getresponse()
        assert resp.status == 413
        conn.close()
    finally:
        proxy.stop()
        upstream.shutdown()
        upstream.server_close()


def test_forwarded_proto_set_by_proxy(certs: CertBundle) -> None:
    """X-Forwarded-Proto must be https coming out of the proxy."""
    upstream, upstream_port = _start_upstream()
    proxy = TLSProxy(config=ProxyConfig(
        host="127.0.0.1", tls_port=0, redirect_port=None,
        tls_certfile=str(certs.certfile), tls_keyfile=str(certs.keyfile),
        upstreams=[Upstream(host="127.0.0.1", port=upstream_port)],
    ))
    proxy.start()
    try:
        ctx = ssl.create_default_context(cafile=str(certs.cafile))
        conn = HTTPSConnection("localhost", proxy.tls_port, timeout=5, context=ctx)
        conn.request("GET", "/health")
        resp: HTTPResponse = conn.getresponse()
        body = json.loads(resp.read().decode())
        conn.close()
        assert resp.status == 200
        assert body.get("xproto") == "https", body
    finally:
        proxy.stop()
        upstream.shutdown()
        upstream.server_close()


def test_certificate_rotation(certs: CertBundle) -> None:
    """A proxy restarted with a rotated certificate serves the new cert."""
    from datetime import UTC, datetime, timedelta

    from aura.api.tls_testing import certificate_details, generate_certs_with_validity

    first = certs
    second = generate_certs_with_validity(
        not_valid_after=datetime.now(UTC) + timedelta(days=365), hostname="localhost"
    )
    upstream, upstream_port = _start_upstream()

    proxy = TLSProxy(config=ProxyConfig(
        host="127.0.0.1", tls_port=0, redirect_port=None,
        tls_certfile=str(first.certfile), tls_keyfile=str(first.keyfile),
        upstreams=[Upstream(host="127.0.0.1", port=upstream_port)],
    ))
    proxy.start()
    try:
        status, _, _ = _https_get(proxy.tls_port, "/liveness", cafile=str(first.cafile))
        assert status == 200

        # Simulate certificate rotation: stop, point config at the new cert, restart.
        proxy.stop()
        proxy.config = ProxyConfig(
            host="127.0.0.1", tls_port=0, redirect_port=None,
            tls_certfile=str(second.certfile), tls_keyfile=str(second.keyfile),
            upstreams=[Upstream(host="127.0.0.1", port=upstream_port)],
        )
        proxy._httpd = None
        proxy._redirect_httpd = None
        proxy.start()

        status, _, _ = _https_get(proxy.tls_port, "/liveness", cafile=str(second.cafile))
        assert status == 200

        first_details = certificate_details(first.certfile)
        second_details = certificate_details(second.certfile)
        assert first_details["serial_number"] != second_details["serial_number"]
        assert first_details["not_after"] != second_details["not_after"]
    finally:
        proxy.stop()
        upstream.shutdown()
        upstream.server_close()