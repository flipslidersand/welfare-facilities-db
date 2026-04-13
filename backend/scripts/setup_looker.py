#!/usr/bin/env python3
"""Setup Looker Studio - Create views and read-only user"""
import os
import sys
import psycopg2
from psycopg2 import sql

sys.path.insert(0, os.path.dirname(__file__) + '/..')

from app.database import engine


def create_looker_user(host: str, database: str, user: str, password: str, looker_password: str = "looker_reader_pass"):
    """Create Looker Studio read-only user"""
    try:
        conn = psycopg2.connect(
            host=host,
            database=database,
            user=user,
            password=password
        )
        cur = conn.cursor()

        # Drop existing user if exists
        try:
            cur.execute("DROP USER IF EXISTS looker_viewer")
            conn.commit()
        except:
            conn.rollback()

        # Create user
        cur.execute(
            sql.SQL("CREATE USER looker_viewer WITH PASSWORD %s"),
            [looker_password]
        )

        # Grant privileges
        cur.execute("GRANT CONNECT ON DATABASE {} TO looker_viewer".format(database))
        cur.execute("GRANT USAGE ON SCHEMA public TO looker_viewer")
        cur.execute("GRANT SELECT ON ALL TABLES IN SCHEMA public TO looker_viewer")

        conn.commit()
        cur.close()
        conn.close()

        print("✓ Looker user created: looker_viewer")
        print(f"  Password: {looker_password}")

    except Exception as e:
        print(f"❌ Error creating Looker user: {e}")
        raise


def create_looker_views(host: str, database: str, user: str, password: str):
    """Create Looker Studio views for aggregated data"""
    try:
        conn = psycopg2.connect(
            host=host,
            database=database,
            user=user,
            password=password
        )
        cur = conn.cursor()

        # View 1: Corporation summary (年度×法人別)
        cur.execute("""
        DROP VIEW IF EXISTS v_corporation_summary CASCADE;
        CREATE VIEW v_corporation_summary AS
        SELECT
            cf.fiscal_year,
            cf.corporation_id,
            c.name,
            c.prefecture,
            c.type,
            cf.revenue,
            COUNT(DISTINCT f.facility_id) AS facility_count,
            COALESCE(SUM(f.capacity), 0) AS total_capacity
        FROM corporation_financials cf
        JOIN corporations c ON cf.corporation_id = c.corporation_id
        LEFT JOIN facilities f ON c.corporation_id = f.corporation_id
        GROUP BY cf.fiscal_year, cf.corporation_id, c.name, c.prefecture, c.type, cf.revenue
        ORDER BY cf.fiscal_year DESC, cf.revenue DESC;
        """)

        # View 2: Regional summary (年度×都道府県別)
        cur.execute("""
        DROP VIEW IF EXISTS v_regional_summary CASCADE;
        CREATE VIEW v_regional_summary AS
        SELECT
            cf.fiscal_year,
            c.prefecture,
            COUNT(DISTINCT cf.corporation_id) AS corporation_count,
            COUNT(DISTINCT f.facility_id) AS facility_count,
            COALESCE(SUM(f.capacity), 0) AS total_capacity,
            COALESCE(SUM(cf.revenue), 0) AS total_revenue,
            ROUND(AVG(f.capacity)::numeric, 2) AS avg_capacity
        FROM corporation_financials cf
        JOIN corporations c ON cf.corporation_id = c.corporation_id
        LEFT JOIN facilities f ON c.corporation_id = f.corporation_id
        GROUP BY cf.fiscal_year, c.prefecture
        ORDER BY cf.fiscal_year DESC, total_revenue DESC;
        """)

        # View 3: Service type summary
        cur.execute("""
        DROP VIEW IF EXISTS v_service_type_summary CASCADE;
        CREATE VIEW v_service_type_summary AS
        SELECT
            f.service_type,
            f.prefecture,
            COUNT(DISTINCT f.facility_id) AS facility_count,
            COALESCE(SUM(f.capacity), 0) AS total_capacity,
            COUNT(DISTINCT f.corporation_id) AS corporation_count
        FROM facilities f
        WHERE f.service_type IS NOT NULL
        GROUP BY f.service_type, f.prefecture
        ORDER BY f.service_type, facility_count DESC;
        """)

        conn.commit()
        cur.close()
        conn.close()

        print("✓ Looker Studio views created:")
        print("  - v_corporation_summary")
        print("  - v_regional_summary")
        print("  - v_service_type_summary")

    except Exception as e:
        print(f"❌ Error creating views: {e}")
        raise


if __name__ == "__main__":
    # Database connection details from environment or command line
    host = os.getenv("DB_HOST", "localhost")
    database = os.getenv("DB_NAME", "welfare_facilities_db")
    user = os.getenv("DB_USER", "dev")
    password = os.getenv("DB_PASSWORD", "devpass")
    looker_password = sys.argv[1] if len(sys.argv) > 1 else "looker_reader_pass"

    print(f"🔧 Setting up Looker Studio for {database}@{host}...")

    try:
        create_looker_user(host, database, user, password, looker_password)
        create_looker_views(host, database, user, password)
        print("\n✅ Looker Studio setup complete!")
        print("   Connection details:")
        print(f"   - Host: {host}")
        print(f"   - Database: {database}")
        print(f"   - User: looker_viewer")
        print(f"   - Password: {looker_password}")
    except Exception as e:
        print(f"\n❌ Setup failed: {e}")
        sys.exit(1)
