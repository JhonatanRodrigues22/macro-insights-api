"""Declarative base para os modelos SQLAlchemy."""

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Classe-base de todos os modelos ORM."""
    pass
