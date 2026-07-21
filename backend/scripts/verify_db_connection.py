#!/usr/bin/env python3

"""
Database Connection Verification Script
データベース接続を確認するスクリプト
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__) + '/..')

from app.database import engine, SessionLocal
from sqlalchemy import text
import json

def verify_connection():
    """Verify database connection and tables"""
    try:
        # Test connection
        with engine.connect() as conn:
            result = conn.execute(text("SELECT NOW();"))
            timestamp = result.fetchone()[0]
            print(f"✓ Database connection successful: {timestamp}")
        
        # Check tables
        inspector = __import__('sqlalchemy').inspect(engine)
        tables = inspector.get_table_names()
        
        expected_tables = {
            'corporations': 'Law person master',
            'facilities': 'Facilities master',
            'corporation_financials': 'Financial data',
            'data_collection_logs': 'Collection logs'
        }
        
        print("\n✓ Database Tables:")
        found_all = True
        for table_name, description in expected_tables.items():
            if table_name in tables:
                # Get column count
                columns = inspector.get_columns(table_name)
                print(f"  ✓ {table_name:<25} ({len(columns)} columns) - {description}")
            else:
                print(f"  ✗ {table_name:<25} - NOT FOUND")
                found_all = False
        
        if found_all:
            print("\n✓ All required tables exist!")
            return True
        else:
            print("\n✗ Some tables are missing. Run init_db.py to initialize.")
            return False
            
    except Exception as e:
        print(f"✗ Database connection failed:")
        print(f"  Error: {str(e)}")
        print(f"\n  Troubleshooting:")
        print(f"  1. Ensure PostgreSQL container is running: docker-compose ps db")
        print(f"  2. Check DATABASE_URL in backend/.env")
        print(f"  3. Wait for DB startup (30 seconds): docker-compose logs db")
        return False

if __name__ == "__main__":
    success = verify_connection()
    sys.exit(0 if success else 1)
