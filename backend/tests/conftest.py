import json
import os
import tempfile
from pathlib import Path

import pytest

FIXTURES = Path(__file__).resolve().parent / "fixtures"

_tmp = Path(tempfile.mkdtemp(prefix="onboarding-tests-"))
os.environ.setdefault("DATABASE_URL", f"sqlite:///{_tmp / 'test.db'}")
os.environ.setdefault("UPLOADS_DIRECTORY", str(_tmp / "uploads"))
os.environ.setdefault("ANTHROPIC_API_KEY", "test-key")


def load_fixture(name: str) -> dict:
    return json.loads((FIXTURES / name).read_text())


@pytest.fixture
def legal_extraction() -> dict:
    return load_fixture("legal_extraction.json")


@pytest.fixture
def banking_extraction() -> dict:
    return load_fixture("banking_extraction.json")


@pytest.fixture
def menu_extraction() -> dict:
    return load_fixture("menu_extraction.json")


@pytest.fixture
def fresh_database():
    from app.database import Base, engine

    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def client(fresh_database):
    from fastapi.testclient import TestClient

    from app.main import app

    with TestClient(app) as test_client:
        yield test_client
