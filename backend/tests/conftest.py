import os
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

TEST_DB_PATH = Path(__file__).parent / "test_app.db"
os.environ["DATABASE_URL"] = f"sqlite:///{TEST_DB_PATH.as_posix()}"
os.environ["JWT_SECRET_KEY"] = "test-secret-key"
os.environ["FRONTEND_ORIGIN"] = "http://localhost:5173"

from app.core.config import get_settings

get_settings.cache_clear()

from app.core.database import engine
from app.main import app
from app.models.base import Base


@pytest.fixture(autouse=True)
def reset_db():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield


@pytest.fixture(scope="session", autouse=True)
def cleanup_db_file():
    yield
    engine.dispose()
    try:
        if TEST_DB_PATH.exists():
            TEST_DB_PATH.unlink()
    except PermissionError:
        # Windows may keep a lock briefly; not critical for test success.
        pass


@pytest.fixture
def client() -> TestClient:
    with TestClient(app) as test_client:
        yield test_client