import os
import hashlib
from datetime import datetime
from fastapi import Security, HTTPException, status, Depends
from fastapi.security.api_key import APIKeyHeader
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.models import ApiKey

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)

FALLBACK_API_KEY = os.getenv("API_KEY", "")


def hash_api_key(key: str) -> str:
    """Hash API key using PBKDF2"""
    return hashlib.pbkdf2_hmac('sha256', key.encode(), b'welfare-facilities-db', 100000).hex()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


async def require_api_key(key: str = Security(api_key_header), db: Session = Depends(get_db)) -> str:
    if not key:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing API key")

    key_hash = hash_api_key(key)

    # Look up key in database
    api_key_record = db.query(ApiKey).filter(
        ApiKey.key_hash == key_hash,
        ApiKey.is_active == True
    ).first()

    if api_key_record:
        # Check expiration
        if api_key_record.expires_at and api_key_record.expires_at < datetime.utcnow():
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="API key expired")

        # Update last_used_at
        api_key_record.last_used_at = datetime.utcnow()
        db.commit()
        return key

    # Fallback to environment variable for bootstrap
    if FALLBACK_API_KEY and key == FALLBACK_API_KEY:
        return key

    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid API key")
