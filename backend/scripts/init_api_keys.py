#!/usr/bin/env python3
"""Initialize default API keys in the database."""

import sys
import os
import logging
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import DATABASE_URL
from app.models import Base, ApiKey
from app.auth import hash_api_key

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def init_api_keys():
    engine = create_engine(DATABASE_URL)
    Session = sessionmaker(bind=engine)
    session = Session()

    try:
        existing_key = session.query(ApiKey).first()
        if existing_key:
            logger.info("API keys already initialized, skipping")
            return

        default_key_plain = os.getenv("API_KEY", "default-key")
        default_key_hash = hash_api_key(default_key_plain)

        default_api_key = ApiKey(
            key_hash=default_key_hash,
            name="Default API Key",
            is_active=True
        )
        session.add(default_api_key)
        session.commit()

        logger.info("Default API key initialized successfully")

    except Exception as e:
        logger.error(f"Failed to initialize API keys: {e}")
        session.rollback()
        raise
    finally:
        session.close()


if __name__ == "__main__":
    init_api_keys()
