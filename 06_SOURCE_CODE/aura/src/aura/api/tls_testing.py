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
        .not_valid_before(_utcnow())
        .not_valid_after(_utcnow(beyond=True))
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

    # 2. Server cert for localhost/127.0.0.1 signed by the CA.
    server_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    server_name = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, "localhost")])
    server_cert = (
        x509.CertificateBuilder()
        .subject_name(server_name)
        .issuer_name(ca_name)
        .public_key(server_key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(_utcnow())
        .not_valid_after(_utcnow(beyond=True))
        .add_extension(
            x509.SubjectAlternativeName(
                [x509.DNSName("localhost"), x509.IPAddress(__import__("ipaddress").ip_address("127.0.0.1"))]
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


def _utcnow(*, beyond: bool = False) -> datetime:
    """Timezone-aware now (or a far-future date) for certificate validity."""
    if beyond:
        return datetime(2049, 12, 31, tzinfo=UTC)
    return datetime.now(UTC)


__all__ = ["CertBundle", "generate_self_signed_certs"]