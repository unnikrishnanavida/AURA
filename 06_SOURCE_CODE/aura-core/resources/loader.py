from pathlib import Path


def load_binary(path: str) -> bytes:
    return Path(path).read_bytes()
