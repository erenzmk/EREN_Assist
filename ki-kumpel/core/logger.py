"""Gemeinsame Logging-Helfer."""
from __future__ import annotations

import logging
from logging.handlers import RotatingFileHandler

from core.config import LOG_FILE

_LOGGER_INITIALISED = False

def get_logger(name: str = "ki_kumpel") -> logging.Logger:
    global _LOGGER_INITIALISED

    logger = logging.getLogger(name)
    if _LOGGER_INITIALISED:
        return logger

    logger.setLevel(logging.INFO)
    formatter = logging.Formatter("[%(asctime)s] %(levelname)s %(name)s: %(message)s")

    file_handler = RotatingFileHandler(LOG_FILE, maxBytes=2_000_000, backupCount=3, encoding="utf-8")
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    _LOGGER_INITIALISED = True
    return logger


def log_line(message: str) -> None:
    get_logger().info(message)
