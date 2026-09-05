from __future__ import annotations

import logging
from typing import Optional

from .formatter import SimpleFormatter


class LoggerFactory:
    def __init__(self, level: int = logging.INFO) -> None:
        self.level = level

    def create(self, name: str, console: bool = True) -> logging.Logger:
        logger = logging.getLogger(name)
        logger.setLevel(self.level)
        if console and not logger.handlers:
            ch = logging.StreamHandler()
            ch.setFormatter(SimpleFormatter())
            logger.addHandler(ch)
        return logger
