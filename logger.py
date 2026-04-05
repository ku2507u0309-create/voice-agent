"""
logger.py – Centralised logging configuration for the AI Voice Agent.

Call ``setup_logger(name)`` once per module to obtain a logger that writes to
both the console (INFO+) and the rotating log file (DEBUG+).
"""

import logging
import sys
from logging.handlers import RotatingFileHandler

from config import LOG_FILE


def setup_logger(name: str = "voice_agent") -> logging.Logger:
    """
    Return a named logger with a console handler (INFO) and a rotating file
    handler (DEBUG).  Calling this multiple times with the same *name* always
    returns the same logger without adding duplicate handlers.
    """
    logger = logging.getLogger(name)

    # Avoid adding duplicate handlers when the module is imported multiple times
    if logger.handlers:
        return logger

    logger.setLevel(logging.DEBUG)

    fmt = logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s")

    # Console – INFO and above
    console = logging.StreamHandler(sys.stdout)
    console.setLevel(logging.INFO)
    console.setFormatter(fmt)
    logger.addHandler(console)

    # Rotating file – DEBUG and above (max 2 MB, 3 backups)
    try:
        file_handler = RotatingFileHandler(
            LOG_FILE, maxBytes=2 * 1024 * 1024, backupCount=3, encoding="utf-8"
        )
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(fmt)
        logger.addHandler(file_handler)
    except OSError as exc:
        logger.warning("Could not open log file '%s': %s", LOG_FILE, exc)

    return logger
