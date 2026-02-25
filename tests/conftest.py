"""Fixtures compartilhadas para os testes."""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db.base import Base
from app.db.session import get_db
from app.main import app

# Banco SQLite em memória para testes
SQLITE_TEST_URL = "sqlite:///./test.db"
engine_test = create_engine(SQLITE_TEST_URL, connect_args={"check_same_thread": False})
TestSession = sessionmaker(bind=engine_test, autocommit=False, autoflush=False)


def override_get_db():
    db = TestSession()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture(autouse=True)
def setup_db():
    """Cria e destrói as tabelas a cada teste."""
    Base.metadata.create_all(bind=engine_test)
    yield
    Base.metadata.drop_all(bind=engine_test)


@pytest.fixture()
def client():
    """TestClient do FastAPI com banco de teste."""
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture()
def db():
    """Sessão de banco de dados para testes unitários."""
    session = TestSession()
    try:
        yield session
    finally:
        session.close()
