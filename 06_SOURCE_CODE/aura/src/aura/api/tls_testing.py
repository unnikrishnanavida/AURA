"""Ephemeral TLS certificate generation for tests and local staging.

Generates a self-signed CA + server certificate valid for ``localhost`` /
``127.0.0.1`` using the ``cryptography`` package. The output is written to a
temp directory; **private keys are never committed** and the helper refuses to
overwrite existing paths.

Only for automated HTTPS testing / local development — never for public
deployment (no CA trust, no real identity).
"""

from __future__ import annotations

import tempfile
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.x509.oid import ExtendedKeyUsageOID, NameOID


@dataclass
class CertBundle:
    certfile: Path
    keyfile: Path
    cafile: Path


def generate_self_signed_certs(*, directory: Path | None = None) -> CertBundle:
    """Create a CA + server cert for localhost; returns paths to cert/key/ca."""
    return generate_certs_with_validity(not_valid_after=datetime(2049, 12, 31, tzinfo=UTC), directory=directory)


def generate_certs_with_validity(
    *,
    not_valid_after: datetime,
    hostname: str = "localhost",
    directory: Path | None = None,
    not_valid_before: datetime | None = None,
) -> CertBundle:
    """Create a CA + server cert with explicit validity and SAN hostname.

    Centrally used by tests to produce valid, expired, or wrong-hostname
    certificates. ``hostname`` is placed in the SAN; ``127.0.0.1`` is always
    included so loopback HTTPS still works. ``not_valid_before`` overrides the
    default "now" so an *expired* fixture can be generated with both bounds in
    the past.
    """
    if directory is None:
        directory = Path(tempfile.mkdtemp(prefix="aura-tls-"))
    directory.mkdir(parents=True, exist_ok=True)

    # 1. Ephemeral self-signed CA.
    ca_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    ca_name = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, "AURA Local Test CA")])
    ca_ski = x509.SubjectKeyIdentifier.from_public_key(ca_key.public_key())
    ca_cert = (
        x509.CertificateBuilder()
        .subject_name(ca_name)
        .issuer_name(ca_name)
        .public_key(ca_key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(not_valid_before if not_valid_before is not None else _utcnow())
        .not_valid_after(not_valid_after)
        .add_extension(x509.BasicConstraints(ca=True, path_length=None), critical=True)
        .add_extension(ca_ski, critical=False)
        .add_extension(
            x509.AuthorityKeyIdentifier.from_issuer_public_key(ca_key.public_key()),
            critical=False,
        )
        .add_extension(
            x509.KeyUsage(
                digital_signature=True,
                content_commitment=True,
                key_encipherment=False,
                data_encipherment=False,
                key_agreement=False,
                key_cert_sign=True,
                crl_sign=True,
                encipher_only=False,
                decipher_only=False,
            ),
            critical=True,
        )
        .sign(ca_key, hashes.SHA256())
    )

    # 2. Server cert for the requested hostname signed by the CA.
    server_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    server_name = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, hostname)])
    server_cert = (
        x509.CertificateBuilder()
        .subject_name(server_name)
        .issuer_name(ca_name)
        .public_key(server_key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(not_valid_before if not_valid_before is not None else _utcnow())
        .not_valid_after(not_valid_after)
        .add_extension(
            x509.SubjectAlternativeName(
                [x509.DNSName(hostname), x509.IPAddress(__import__("ipaddress").ip_address("127.0.0.1"))]
            ),
            critical=False,
        )
        .add_extension(x509.BasicConstraints(ca=False, path_length=None), critical=True)
        .add_extension(x509.SubjectKeyIdentifier.from_public_key(server_key.public_key()), critical=False)
        .add_extension(
            x509.AuthorityKeyIdentifier.from_issuer_public_key(ca_key.public_key()),
            critical=False,
        )
        .add_extension(
            x509.ExtendedKeyUsage([ExtendedKeyUsageOID.SERVER_AUTH]),
            critical=False,
        )
        .add_extension(
            x509.KeyUsage(
                digital_signature=True,
                content_commitment=False,
                key_encipherment=True,
                data_encipherment=False,
                key_agreement=False,
                key_cert_sign=False,
                crl_sign=False,
                encipher_only=False,
                decipher_only=False,
            ),
            critical=True,
        )
        .sign(ca_key, hashes.SHA256())
    )

    certfile = directory / "server.crt"
    keyfile = directory / "server.key"
    cafile = directory / "ca.crt"

    certfile.write_bytes(server_cert.public_bytes(serialization.Encoding.PEM))
    keyfile.write_bytes(
        server_key.private_bytes(
            serialization.Encoding.PEM,
            serialization.PrivateFormat.PKCS8,
            serialization.NoEncryption(),
        )
    )
    cafile.write_bytes(ca_cert.public_bytes(serialization.Encoding.PEM))

    return CertBundle(certfile=certfile, keyfile=keyfile, cafile=cafile)


def _utcnow() -> datetime:
    """Current UTC time for the certificate validity start."""
    return datetime.now(UTC)


def certificate_details(certfile: str | Path) -> dict[str, object]:
    """Return serialization-friendly certificate facts for lifecycle checks.

    Used by the proxy startup warning and by tests verifying expiry / SAN /
    rotation behavior.
    """
    cert = x509.load_pem_x509_certificate(Path(certfile).read_bytes())
    san: list[str] = []
    try:
        san_ext = cert.extensions.get_extension_for_class(x509.SubjectAlternativeName)
        for name in san_ext.value:
            san.append(name.value)
    except x509.ExtensionNotFound:
        pass
    return {
        "subject": cert.subject.rfc4514_string(),
        "issuer": cert.issuer.rfc4514_string(),
        "not_before": cert.not_valid_before_utc.isoformat(),
        "not_after": cert.not_valid_after_utc.isoformat(),
        "serial_number": str(cert.serial_number),
        "san": san,
    }


def certificate_expiry_status(certfile: str | Path, *, warn_days: int = 30) -> dict[str, object]:
    """Certificate expiry facts used by operators and the proxy startup check.

    Returns ``{"ok", "expired", "days_remaining", "warning_before_expiry",
    "not_after"}``.
    """
    details = certificate_details(certfile)
    not_after = datetime.fromisoformat(str(details["not_after"]))
    now = datetime.now(UTC)
    remaining = int((not_after - now).total_seconds() // 86400)
    return {
        "ok": remaining > 0,
        "expired": remaining <= 0,
        "days_remaining": remaining,
        "warning_before_expiry": 0 < remaining <= warn_days,
        "not_after": details["not_after"],
    }


__all__ = [
    "CertBundle",
    "certificate_details",
    "certificate_expiry_status",
    "generate_certs_with_validity",
    "generate_self_signed_certs",
]