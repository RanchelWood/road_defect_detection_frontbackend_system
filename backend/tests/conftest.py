import os
import shutil
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

TEST_DB_PATH = Path(__file__).parent / "test_app.db"
TEST_MEDIA_ROOT = Path(__file__).parent / "test_media"
os.environ["DATABASE_URL"] = f"sqlite:///{TEST_DB_PATH.as_posix()}"
os.environ["JWT_SECRET_KEY"] = "test-secret-key"
os.environ["FRONTEND_ORIGIN"] = "http://localhost:5173"
os.environ["MEDIA_ROOT"] = str(TEST_MEDIA_ROOT)
os.environ["INFERENCE_AUTORUN_ENABLED"] = "false"

from app.core.config import get_settings

get_settings.cache_clear()

from app.core.database import SessionLocal, engine
from app.main import app
from app.models.base import Base


@pytest.fixture(autouse=True)
def reset_db():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield


@pytest.fixture(scope="session", autouse=True)
def cleanup_test_artifacts():
    yield
    engine.dispose()

    try:
        if TEST_DB_PATH.exists():
            TEST_DB_PATH.unlink()
    except PermissionError:
        pass

    if TEST_MEDIA_ROOT.exists():
        shutil.rmtree(TEST_MEDIA_ROOT, ignore_errors=True)


@pytest.fixture
def client() -> TestClient:
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def db_session():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()