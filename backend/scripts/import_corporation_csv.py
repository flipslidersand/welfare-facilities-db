#!/usr/bin/env python3
"""Import corporation financial data from CSV files"""
import os
import sys
import pandas as pd
from datetime import datetime

sys.path.insert(0, os.path.dirname(__file__) + '/..')

from app.database import SessionLocal
from app.models import Corporation, CorporationFinancial


def import_corporations_from_csv(csv_file_path: str):
    """
    Import corporation master data from CSV file

    Expected CSV columns:
    - corporation_id (法人番号)
    - name (法人名称)
    - type (法人種別)
    - postal_code (郵便番号)
    - prefecture (都道府県)
    - city (市区町村)
    - address (詳細住所)
    - established_date (設立年月)
    """
    if not os.path.exists(csv_file_path):
        print(f"❌ File not found: {csv_file_path}")
        return 0

    try:
        df = pd.read_csv(csv_file_path, dtype=str)
        print(f"📂 Read {len(df)} corporation rows from {csv_file_path}")

        db = SessionLocal()
        count = 0

        for _, row in df.iterrows():
            corporation_id = row.get('corporation_id', '').strip()
            if not corporation_id:
                continue

            # Check if corporation already exists
            existing = db.query(Corporation).filter_by(corporation_id=corporation_id).first()

            if existing:
                existing.name = row.get('name', '')
                existing.type = row.get('type', '')
                existing.postal_code = row.get('postal_code', '')
                existing.prefecture = row.get('prefecture', '')
                existing.city = row.get('city', '')
                existing.address = row.get('address', '')
                existing.established_date = pd.to_datetime(row.get('established_date', '')).date() if pd.notna(row.get('established_date')) else None
                existing.updated_at = datetime.utcnow()
            else:
                corporation = Corporation(
                    corporation_id=corporation_id,
                    name=row.get('name', ''),
                    type=row.get('type', ''),
                    postal_code=row.get('postal_code', ''),
                    prefecture=row.get('prefecture', ''),
                    city=row.get('city', ''),
                    address=row.get('address', ''),
                    established_date=pd.to_datetime(row.get('established_date', '')).date() if pd.notna(row.get('established_date')) else None,
                    updated_at=datetime.utcnow()
                )
                db.add(corporation)

            count += 1

        db.commit()
        db.close()
        print(f"✓ Imported {count} corporations")
        return count

    except Exception as e:
        print(f"❌ Error importing corporations: {e}")
        return 0


def import_financials_from_csv(csv_file_path: str):
    """
    Import corporation financial data from CSV file

    Expected CSV columns:
    - corporation_id (法人番号)
    - fiscal_year (対象年度)
    - revenue (売上高)
    - ordinary_profit (経常利益)
    - net_assets (純資産額)
    - total_assets (総資産額)
    - employees (常勤換算職員数)
    - report_url (報告書URL)
    """
    if not os.path.exists(csv_file_path):
        print(f"❌ File not found: {csv_file_path}")
        return 0

    try:
        df = pd.read_csv(csv_file_path, dtype=str)
        print(f"📂 Read {len(df)} financial rows from {csv_file_path}")

        db = SessionLocal()
        count = 0

        for _, row in df.iterrows():
            corporation_id = row.get('corporation_id', '').strip()
            fiscal_year_str = row.get('fiscal_year', '').strip()

            if not corporation_id or not fiscal_year_str:
                continue

            try:
                fiscal_year = int(fiscal_year_str)
            except ValueError:
                continue

            # Check if financial record already exists
            existing = db.query(CorporationFinancial).filter_by(
                corporation_id=corporation_id,
                fiscal_year=fiscal_year
            ).first()

            def safe_int(val):
                try:
                    return int(float(val.strip())) if val.strip() else None
                except:
                    return None

            if existing:
                existing.revenue = safe_int(row.get('revenue', ''))
                existing.ordinary_profit = safe_int(row.get('ordinary_profit', ''))
                existing.net_assets = safe_int(row.get('net_assets', ''))
                existing.total_assets = safe_int(row.get('total_assets', ''))
                existing.employees = safe_int(row.get('employees', ''))
                existing.report_url = row.get('report_url', '')
                existing.updated_at = datetime.utcnow()
            else:
                financial = CorporationFinancial(
                    corporation_id=corporation_id,
                    fiscal_year=fiscal_year,
                    revenue=safe_int(row.get('revenue', '')),
                    ordinary_profit=safe_int(row.get('ordinary_profit', '')),
                    net_assets=safe_int(row.get('net_assets', '')),
                    total_assets=safe_int(row.get('total_assets', '')),
                    employees=safe_int(row.get('employees', '')),
                    report_url=row.get('report_url', ''),
                    collected_at=datetime.utcnow(),
                    updated_at=datetime.utcnow()
                )
                db.add(financial)

            count += 1

        db.commit()
        db.close()
        print(f"✓ Imported {count} financial records")
        return count

    except Exception as e:
        print(f"❌ Error importing financials: {e}")
        return 0


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python import_corporation_csv.py --master <corporations.csv>")
        print("  python import_corporation_csv.py --financials <financials.csv>")
        sys.exit(1)

    mode = sys.argv[1]
    csv_file = sys.argv[2] if len(sys.argv) > 2 else None

    if not csv_file:
        print("❌ CSV file not specified")
        sys.exit(1)

    if mode == "--master":
        import_corporations_from_csv(csv_file)
    elif mode == "--financials":
        import_financials_from_csv(csv_file)
    else:
        print(f"❌ Unknown mode: {mode}")
        sys.exit(1)
