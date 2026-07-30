import secrets


def token_hex(nbytes: int = 32) -> str:
    return secrets.token_hex(nbytes)
