import pytest
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient
from unittest.mock import patch

os.environ.setdefault("API_KEY", "test-api-key")
os.environ.setdefault("PBKDF2_SALT", "test-salt")

from app.database import Base, get_db
from app.main import app
from app.models import ApiKey
from app.auth import hash_api_key

SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"

engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function")
def db():
    Base.metadata.create_all(bind=engine)
    yield TestingSessionLocal()
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(db):
    def override_get_db():
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db

    with patch("app.scheduler.start_scheduler"), patch("app.scheduler.stop_scheduler"):
        yield TestClient(app)

    app.dependency_overrides.clear()


@pytest.fixture
def test_api_key(db):
    plain_key = os.environ["API_KEY"]
    key_hash = hash_api_key(plain_key)
    api_key = ApiKey(
        key_hash=key_hash,
        name="Test Key",
        is_active=True
    )
    db.add(api_key)
    db.commit()
    db.refresh(api_key)
    return {"id": api_key.id, "plain": plain_key, "db": api_key}
