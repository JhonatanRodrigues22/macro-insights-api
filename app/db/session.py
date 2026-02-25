"""Gerenciamento da sessão do banco de dados."""

from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import settings
from app.db.base import Base

engine = create_engine(
    settings.DATABASE_URL,
    connect_args={"check_same_thread": False},  # necessário para SQLite
    echo=settings.DEBUG,
)

SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)


def init_db() -> None:
    """Cria todas as tabelas no banco (idempotente)."""
    Base.metadata.create_all(bind=engine)


def get_db() -> Generator[Session, None, None]:
    """Dependency do FastAPI que fornece uma sessão de banco."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
