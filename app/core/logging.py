"""Configuração centralizada de logging."""

import logging
import sys

from app.core.config import settings


def setup_logging() -> logging.Logger:
    """Cria e configura o logger principal da aplicação."""
    level = logging.DEBUG if settings.DEBUG else logging.INFO

    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)

    logger = logging.getLogger("macro_insights")
    logger.setLevel(level)
    logger.addHandler(handler)

    return logger


logger = setup_logging()
