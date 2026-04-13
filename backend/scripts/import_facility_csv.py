#!/usr/bin/env python3
"""Import facility data from CSV files"""
import os
import sys
import pandas as pd
from datetime import datetime

sys.path.insert(0, os.path.dirname(__file__) + '/..')

from app.database import SessionLocal
from app.models import Facility, Corporation


def import_facilities_from_csv(csv_file_path: str, service_type: str):
    """
    Import facilities from CSV file

    Expected CSV columns:
    - facility_id (事業所番号)
    - facility_name (事業所名称)
    - corporation_id (法人番号) - optional
    - service_type (サービス種別)
    - service_detail (具体的サービス)
    - capacity (定員)
    - opened_date (開設年月)
    - postal_code (郵便番号)
    - prefecture (都道府県)
    - city (市区町村)
    - address (詳細住所)
    - management_type (経営主体種別)
    """
    if not os.path.exists(csv_file_path):
        print(f"❌ File not found: {csv_file_path}")
        return 0

    try:
        df = pd.read_csv(csv_file_path, dtype=str)
        print(f"📂 Read {len(df)} rows from {csv_file_path}")

        db = SessionLocal()
        count = 0

        for _, row in df.iterrows():
            facility_id = row.get('facility_id', '').strip()
            if not facility_id:
                continue

            # Check if facility already exists
            existing = db.query(Facility).filter_by(facility_id=facility_id).first()

            corporation_id = row.get('corporation_id', '').strip() or None
            match_status = 'matched' if corporation_id else 'unmatched'

            # Create or update facility
            if existing:
                existing.name = row.get('facility_name', '')
                existing.corporation_id = corporation_id
                existing.service_type = service_type
                existing.service_detail = row.get('service_detail', '')
                existing.capacity = int(row.get('capacity', 0)) if row.get('capacity', '').strip().isdigit() else None
                existing.opened_date = pd.to_datetime(row.get('opened_date', '')).date() if pd.notna(row.get('opened_date')) else None
                existing.postal_code = row.get('postal_code', '')
                existing.prefecture = row.get('prefecture', '')
                existing.city = row.get('city', '')
                existing.address = row.get('address', '')
                existing.management_type = row.get('management_type', '')
                existing.match_status = match_status
                existing.updated_at = datetime.utcnow()
            else:
                facility = Facility(
                    facility_id=facility_id,
                    name=row.get('facility_name', ''),
                    corporation_id=corporation_id,
                    service_type=service_type,
                    service_detail=row.get('service_detail', ''),
                    capacity=int(row.get('capacity', 0)) if row.get('capacity', '').strip().isdigit() else None,
                    opened_date=pd.to_datetime(row.get('opened_date', '')).date() if pd.notna(row.get('opened_date')) else None,
                    postal_code=row.get('postal_code', ''),
                    prefecture=row.get('prefecture', ''),
                    city=row.get('city', ''),
                    address=row.get('address', ''),
                    management_type=row.get('management_type', ''),
                    match_status=match_status,
                    updated_at=datetime.utcnow()
                )
                db.add(facility)

            # Auto-create corporation if it doesn't exist
            if corporation_id and not db.query(Corporation).filter_by(corporation_id=corporation_id).first():
                corporation = Corporation(
                    corporation_id=corporation_id,
                    name=row.get('corporation_name', 'Unknown'),
                    prefecture=row.get('prefecture', ''),
                    updated_at=datetime.utcnow()
                )
                db.add(corporation)

            count += 1

        db.commit()
        db.close()
        print(f"✓ Imported {count} facilities")
        return count

    except Exception as e:
        print(f"❌ Error importing facilities: {e}")
        return 0


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python import_facility_csv.py <csv_file> [service_type]")
        print("Example: python import_facility_csv.py facilities.csv 介護")
        sys.exit(1)

    csv_file = sys.argv[1]
    service_type = sys.argv[2] if len(sys.argv) > 2 else "介護"

    import_facilities_from_csv(csv_file, service_type)
