#!/usr/bin/env python3
"""Import facility data from CSV files with collection logging"""
import os
import sys
import pandas as pd
from datetime import datetime

sys.path.insert(0, os.path.dirname(__file__) + '/..')

from app.database import SessionLocal
from app.models import Facility, Corporation, DataCollectionLog

# WAM NET 障害福祉サービス等情報公表 CSV column mapping
# Actual column names → internal field names
WAM_NET_SFK_COLUMNS = {
    "事業所番号": "facility_id",
    "事業所の名称": "facility_name",
    "法人番号": "corporation_id",
    "法人の名称": "corporation_name",
    "サービス種別": "service_type",
    "定員": "capacity",
    "事業所住所（市区町村）": "city",   # 都道府県+市区町村が連結
    "事業所住所（番地以降）": "address",
    "都道府県コード又は市区町村コード": "pref_city_code",
}

# 都道府県コード → 都道府県名マッピング (2桁 prefix)
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


def _normalize_row(row: pd.Series) -> dict:
    """WAM NET CSV の行を内部フィールド名に変換する。"""
    result = {}
    for csv_col, field in WAM_NET_SFK_COLUMNS.items():
        val = row.get(csv_col, "")
        result[field] = "" if pd.isna(val) else str(val).strip()

    # 都道府県コードから都道府県名を抽出
    pref_code = result.get("pref_city_code", "")[:2]
    result["prefecture"] = PREF_CODE_MAP.get(pref_code, "")

    # フォールバック: 英語カラム名がある場合はそちらを優先（旧形式 CSV 対応）
    for field in ("facility_id", "facility_name", "corporation_id", "service_type", "capacity",
                  "city", "address", "prefecture"):
        if not result.get(field) and row.get(field):
            result[field] = str(row.get(field, "")).strip()

    return result


def log_collection(script_name: str, status: str, records: int = 0, error_msg: str = None):
    """Log data collection event"""
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


def import_facilities_from_csv(csv_file_path: str, service_type: str, data_source: str = "障害公表"):
    """
    Import facilities from CSV file.

    WAM NET 障害福祉サービス等情報公表 CSV の実カラム名:
      事業所番号, 事業所の名称, 法人番号, 法人の名称, サービス種別, 定員,
      事業所住所（市区町村）, 事業所住所（番地以降）,
      都道府県コード又は市区町村コード（都道府県コードは先頭2桁）
    WAM_NET_SFK_COLUMNS で内部フィールド名にマッピングする。
    旧形式（英語カラム名）の CSV にも _normalize_row() でフォールバック対応。
    """
    if not os.path.exists(csv_file_path):
        print(f"❌ File not found: {csv_file_path}")
        return 0

    try:
        df = pd.read_csv(csv_file_path, dtype=str, encoding="utf-8-sig")
        print(f"📂 Read {len(df)} rows from {csv_file_path}")

        db = SessionLocal()
        count = 0

        for _, raw_row in df.iterrows():
            row = _normalize_row(raw_row)
            facility_id = row.get("facility_id", "").strip()
            if not facility_id:
                continue

            existing = db.query(Facility).filter_by(facility_id=facility_id).first()
            corporation_id = row.get("corporation_id", "").strip() or None
            match_status = "matched" if corporation_id else "unmatched"
            cap_str = row.get("capacity", "").strip()
            capacity = int(cap_str) if cap_str.isdigit() else None
            svc_type = row.get("service_type", service_type) or service_type

            if existing:
                existing.name = row.get("facility_name", "")
                existing.corporation_id = corporation_id
                existing.service_type = svc_type
                existing.service_detail = row.get("service_detail", "")
                existing.capacity = capacity
                existing.opened_date = None
                existing.postal_code = row.get("postal_code", "")
                existing.prefecture = row.get("prefecture", "")
                existing.city = row.get("city", "")
                existing.address = row.get("address", "")
                existing.management_type = row.get("management_type", "")
                existing.match_status = match_status
                existing.updated_at = datetime.utcnow()
            else:
                facility = Facility(
                    facility_id=facility_id,
                    name=row.get("facility_name", ""),
                    corporation_id=corporation_id,
                    service_type=svc_type,
                    service_detail=row.get("service_detail", ""),
                    capacity=capacity,
                    opened_date=None,
                    postal_code=row.get("postal_code", ""),
                    prefecture=row.get("prefecture", ""),
                    city=row.get("city", ""),
                    address=row.get("address", ""),
                    management_type=row.get("management_type", ""),
                    match_status=match_status,
                    updated_at=datetime.utcnow(),
                )
                db.add(facility)

            if corporation_id and not db.query(Corporation).filter_by(corporation_id=corporation_id).first():
                corporation = Corporation(
                    corporation_id=corporation_id,
                    name=row.get("corporation_name", "Unknown"),
                    prefecture=row.get("prefecture", ""),
                    updated_at=datetime.utcnow(),
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
        print("Usage: python import_facility_csv.py <csv_file> [service_type] [data_source]")
        print("Example: python import_facility_csv.py facilities.csv 介護 介護公表")
        print("Supported data_source: 介護公表, 障害公表, 児童公表")
        sys.exit(1)

    csv_file = sys.argv[1]
    service_type = sys.argv[2] if len(sys.argv) > 2 else "介護"
    data_source = sys.argv[3] if len(sys.argv) > 3 else "介護公表"

    try:
        log_collection("import_facility_csv", "running")
        records = import_facilities_from_csv(csv_file, service_type, data_source)
        log_collection("import_facility_csv", "success", records_processed=records)
    except Exception as e:
        log_collection("import_facility_csv", "failed", error_msg=str(e))
        print(f"❌ Import failed: {e}")
