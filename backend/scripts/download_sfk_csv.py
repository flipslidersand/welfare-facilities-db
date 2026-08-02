#!/usr/bin/env python3
"""
Download disability welfare facility CSV from WAM NET (障害福祉サービス等情報公表)
URL pattern: https://www.wam.go.jp/content/files/pcpub/top/sfkopendata/YYYYMM/sfkopendata_YYYYMM_NN.zip
"""
import os
import sys
import zipfile
import tempfile
import requests
from datetime import datetime, date
from pathlib import Path

BASE_URL = "https://www.wam.go.jp/content/files/pcpub/top/sfkopendata"

# Service type codes (known valid indices as of 202603)
KNOWN_INDICES = [
    11, 12, 13, 14, 15,          # 居宅介護系
    21, 22, 24,                   # 生活介護系
    32, 33, 34,                   # 就労系
    41, 42, 45, 46,               # 入所系
    52, 53, 54,                   # 児童系
    60, 61, 62, 63, 64, 65, 66, 67, 68, 69, 70,  # その他
]


def latest_yearmonth() -> str:
    """Scrape WAM NET page to get the latest available yearmonth (YYYYMM)."""
    import re
    page_url = "https://www.wam.go.jp/content/wamnet/pcpub/top/sfkopendata/"
    try:
        resp = requests.get(page_url, timeout=15)
        html = resp.content.decode("shift-jis", errors="replace")
        # Extract YYYYMM from download link patterns e.g. /sfkopendata/202603/
        matches = re.findall(r"/sfkopendata/(\d{6})/", html)
        if matches:
            return max(matches)
    except Exception:
        pass
    # Fallback: 3-month lag heuristic
    today = date.today()
    month = today.month - 3
    year = today.year
    if month <= 0:
        month += 12
        year -= 1
    return f"{year}{month:02d}"


def download_zip(yearmonth: str, index: int, dest_dir: Path) -> Path | None:
    url = f"{BASE_URL}/{yearmonth}/sfkopendata_{yearmonth}_{index}.zip"
    resp = requests.get(url, timeout=30)
    if resp.status_code != 200:
        return None

    zip_path = dest_dir / f"sfkopendata_{yearmonth}_{index}.zip"
    zip_path.write_bytes(resp.content)
    return zip_path


def extract_csv(zip_path: Path, dest_dir: Path) -> list[Path]:
    csvs = []
    with zipfile.ZipFile(zip_path) as zf:
        for name in zf.namelist():
            if name.endswith(".csv"):
                zf.extract(name, dest_dir)
                csvs.append(dest_dir / name)
    return csvs


def download_all(yearmonth: str, output_dir: str) -> list[str]:
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)

    csv_files = []
    for idx in KNOWN_INDICES:
        zip_path = download_zip(yearmonth, idx, out)
        if zip_path is None:
            print(f"  skip: {idx} (not found)")
            continue

        csvs = extract_csv(zip_path, out)
        zip_path.unlink()
        for csv in csvs:
            print(f"  ✓ {csv.name} (index={idx})")
            csv_files.append(str(csv))

    return csv_files


if __name__ == "__main__":
    yearmonth = sys.argv[1] if len(sys.argv) > 1 else latest_yearmonth()
    output_dir = sys.argv[2] if len(sys.argv) > 2 else f"/tmp/sfk_csv_{yearmonth}"

    print(f"Downloading SFK CSV: yearmonth={yearmonth} → {output_dir}")
    files = download_all(yearmonth, output_dir)
    print(f"\n✓ {len(files)} CSV files downloaded to {output_dir}")
    for f in files:
        print(f"  {f}")
