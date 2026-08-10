#!/usr/bin/env python3
"""Initialize default API keys in database"""
import sys
import secrets
import hashlib
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.database import SessionLocal
from app.models import ApiKey


def hash_api_key(key: str) -> str:
    """Hash API key using PBKDF2"""
    return hashlib.pbkdf2_hmac('sha256', key.encode(), b'welfare-facilities-db', 100000).hex()


def init_default_keys():
    """Create initial API keys"""
    db = SessionLocal()

    try:
        # Check if keys already exist
        existing = db.query(ApiKey).count()
        if existing > 0:
            print(f"✓ Database already has {existing} API key(s). Skipping initialization.")
            return

        # Generate default key
        default_key = secrets.token_urlsafe(32)
        default_hash = hash_api_key(default_key)

        # Create first key with 1-year expiration
        api_key = ApiKey(
            key_hash=default_hash,
            name="default-key",
            expires_at=datetime.utcnow() + timedelta(days=365),
            is_active=True
        )
        db.add(api_key)
        db.commit()

        print(f"✅ Default API key created:")
        print(f"   Name: default-key")
        print(f"   Key:  {default_key}")
        print(f"   Expires: {api_key.expires_at.strftime('%Y-%m-%d')}")
        print(f"\n⚠️  Save this key securely. You won't see it again!")
        print(f"   Use as X-API-Key header in requests.")

    except Exception as e:
        print(f"❌ Failed to initialize API keys: {e}")
        db.rollback()
        sys.exit(1)
    finally:
        db.close()


if __name__ == "__main__":
    init_default_keys()
