import pytest
from datetime import datetime, timezone, timedelta
from app.models import ApiKey
from app.auth import hash_api_key


def test_api_key_creation(db):
    key_hash = hash_api_key("test-key")
    api_key = ApiKey(
        key_hash=key_hash,
        name="Test Key",
        is_active=True
    )
    db.add(api_key)
    db.commit()
    db.refresh(api_key)

    assert api_key.id is not None
    assert api_key.name == "Test Key"
    assert api_key.is_active is True
    assert api_key.created_at is not None
    assert api_key.usage_count == 0


def test_api_key_with_expiration(db):
    key_hash = hash_api_key("test-key")
    expires_at = datetime.now(timezone.utc) + timedelta(days=30)
    api_key = ApiKey(
        key_hash=key_hash,
        name="Expiring Key",
        expires_at=expires_at
    )
    db.add(api_key)
    db.commit()
    db.refresh(api_key)

    assert api_key.expires_at is not None
    assert isinstance(api_key.expires_at, datetime)


def test_api_key_deactivation(db, test_api_key):
    api_key = test_api_key["db"]
    api_key.is_active = False
    db.commit()

    queried = db.query(ApiKey).filter(ApiKey.id == api_key.id).first()
    assert queried.is_active is False
