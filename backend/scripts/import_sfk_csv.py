#!/usr/bin/env python3
"""
Import WAM NET disability welfare facility CSV (障害福祉サービス等情報公表)
Handles WAM NET column names → DB model mapping.
"""
import os
import sys
import pandas as pd
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.database import SessionLocal
from app.models import Facility, Corporation, DataCollectionLog

PREF_CODE_MAP = {
    "01": "北海道", "02": "青森県", "03": "岩手県", "04": "宮城県", "05": "秋田県",
    "06": "山形県", "07": "福島県", "08": "茨城県", "09": "栃木県", "10": "群馬県",
    "11": "埼玉県", "12": "千葉県", "13": "東京都", "14": "神奈川県", "15": "新潟県",
    "16": "富山県", "17": "石川県", "18": "福井県", "19": "山梨県", "20": "長野県",
    "21": "岐阜県", "22": "静岡県", "23": "愛知県", "24": "三重県", "25": "滋賀県",
    "26": "京都府", "27": "大阪府", "28": "兵庫県", "29": "奈良県", "30": "和歌山県",
    "31": "鳥取県", "32": "島根県", "33": "岡山県", "34": "広島県", "35": "山口県",
    "36": "徳島県", "37": "香川県", "38": "愛媛県", "39": "高知県", "40": "福岡県",
    "41": "佐賀県", "42": "長崎県", "43": "熊本県", "44": "大分県", "45": "宮崎県",
    "46": "鹿児島県", "47": "沖縄県",
}


def pref_code_to_name(code: str) -> str:
    return PREF_CODE_MAP.get(str(code)[:2], "")


def log_collection(script_name: str, status: str, records: int = 0, error_msg: str = None):
    db = SessionLocal()
    try:
        log = DataCollectionLog(
            script_name=script_name,
            status=status,
            records_processed=records,
            error_message=error_msg,
            started_at=datetime.utcnow(),
            completed_at=datetime.utcnow() if status != "running" else None,
        )
        db.add(log)
        db.commit()
    finally:
        db.close()


def import_sfk_csv(csv_path: str) -> int:
    df = pd.read_csv(csv_path, encoding="utf-8", dtype=str)
    print(f"  📂 {Path(csv_path).name}: {len(df)} rows")

    db = SessionLocal()
    count = 0

    for _, row in df.iterrows():
        facility_id = (row.get("事業所番号") or "").strip()
        if not facility_id:
            continue

        pref_code = (row.get("都道府県コード又は市区町村コード") or "").strip()
        prefecture = pref_code_to_name(pref_code)
        corporation_id = (row.get("法人番号") or "").strip() or None
        service_type = (row.get("サービス種別") or "").strip()
        capacity_str = (row.get("定員") or "").strip()
        capacity = int(capacity_str) if capacity_str.isdigit() else None

        facility_data = dict(
            name=(row.get("事業所の名称") or "").strip(),
            corporation_id=corporation_id,
            service_type=service_type,
            service_detail="",
            capacity=capacity,
            opened_date=None,
            postal_code="",
            prefecture=prefecture,
            city=(row.get("事業所住所（市区町村）") or "").strip(),
            address=(row.get("事業所住所（番地以降）") or "").strip(),
            management_type="",
            match_status="matched" if corporation_id else "unmatched",
            updated_at=datetime.utcnow(),
        )

        existing = db.query(Facility).filter_by(facility_id=facility_id).first()
        if existing:
            for k, v in facility_data.items():
                setattr(existing, k, v)
        else:
            db.add(Facility(facility_id=facility_id, **facility_data))

        # Auto-create corporation record if missing
        if corporation_id:
            corp_name = (row.get("法人の名称") or "").strip()
            if corp_name and not db.query(Corporation).filter_by(corporation_id=corporation_id).first():
                db.add(Corporation(
                    corporation_id=corporation_id,
                    name=corp_name,
                    prefecture=prefecture,
                    updated_at=datetime.utcnow(),
                ))

        count += 1

    db.commit()
    db.close()
    return count


def import_all(csv_dir: str) -> int:
    total = 0
    for csv_path in sorted(Path(csv_dir).glob("*.csv")):
        total += import_sfk_csv(str(csv_path))
    return total


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python import_sfk_csv.py <csv_file_or_dir>")
        sys.exit(1)

    target = sys.argv[1]
    log_collection("import_sfk_csv", "running")
    try:
        if Path(target).is_dir():
            records = import_all(target)
        else:
            records = import_sfk_csv(target)
        print(f"✓ Total imported: {records}")
        log_collection("import_sfk_csv", "success", records)
    except Exception as e:
        log_collection("import_sfk_csv", "failed", error_msg=str(e))
        print(f"❌ {e}")
        sys.exit(1)
