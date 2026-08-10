import os
import hashlib
import secrets
from datetime import datetime, timezone
from fastapi import Security, HTTPException, status, Depends
from fastapi.security.api_key import APIKeyHeader
from sqlalchemy.orm import Session
from .database import get_db
from .models import ApiKey

API_KEY = os.getenv("API_KEY", "")
PBKDF2_SALT = os.getenv("PBKDF2_SALT", "welfare-facilities-db").encode()
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


def hash_api_key(key: str) -> str:
    return hashlib.pbkdf2_hmac('sha256', key.encode(), PBKDF2_SALT, 100000).hex()


def verify_api_key(plain_key: str, key_hash: str) -> bool:
    return hash_api_key(plain_key) == key_hash


def generate_api_key() -> str:
    return secrets.token_urlsafe(32)


async def require_api_key(key: str = Security(api_key_header), db: Session = Depends(get_db)) -> str:
    if not key:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing API key")

    if not API_KEY:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="API key not configured")

    api_key_record = db.query(ApiKey).filter(
        ApiKey.key_hash == hash_api_key(key),
        ApiKey.is_active == True
    ).first()

    if not api_key_record:
        if key != API_KEY:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid API key")
        return key

    if api_key_record.expires_at and api_key_record.expires_at < datetime.now(timezone.utc):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="API key expired")

    api_key_record.last_used_at = datetime.now(timezone.utc)
    api_key_record.usage_count += 1
    db.commit()

    return key
