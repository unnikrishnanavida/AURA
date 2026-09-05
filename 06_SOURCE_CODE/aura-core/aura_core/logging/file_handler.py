from __future__ import annotations

import logging
from logging.handlers import RotatingFileHandler


class FileHandler(RotatingFileHandler):
    def __init__(self, filename: str, max_bytes: int = 10_485_760, backup_count: int = 5):
        super().__init__(filename, maxBytes=max_bytes, backupCount=backup_count)
