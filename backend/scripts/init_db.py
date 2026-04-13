#!/usr/bin/env python3
"""Initialize database - Create tables from models"""
import os
import sys
sys.path.insert(0, os.path.dirname(__file__) + '/..')

from app.database import engine, Base
from app.models import Corporation, Facility, CorporationFinancial


def init_db():
    """Create all tables"""
    print("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    print("✓ Database initialized successfully")


if __name__ == "__main__":
    init_db()
