from __future__ import annotations

from logging.handlers import RotatingFileHandler


def rotating_handler(filename: str, max_bytes: int = 10_485_760, backup_count: int = 5) -> RotatingFileHandler:
    return RotatingFileHandler(filename, maxBytes=max_bytes, backupCount=backup_count)
