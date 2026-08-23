"""Lightweight network helpers for aura-memory."""

import socket


def resolve_hostname(host: str) -> str:
    if host in {"localhost", "127.0.0.1", "::1"}:
        return "127.0.0.1"
    try:
        resolved = socket.gethostbyname(host)
        return resolved if resolved else host
    except Exception:
        return host


__all__ = ["resolve_hostname"]
