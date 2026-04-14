#!/usr/bin/env python3
"""Daily PostgreSQL backup script using pg_dump"""
import os
import sys
import subprocess
from datetime import datetime, timedelta
from pathlib import Path

# Configuration (from environment variables)
BACKUP_DIR = Path(os.getenv("BACKUP_DIR", "/backups"))
RETENTION_DAYS = int(os.getenv("BACKUP_RETENTION_DAYS", "7"))
DB_HOST = os.getenv("DB_HOST", "db")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "welfare_facilities_db")
DB_USER = os.getenv("DB_USER", "dev")
DB_PASSWORD = os.getenv("DB_PASSWORD", "devpass")


def run_backup() -> tuple[bool, str, str]:
    """
    Run pg_dump to create a backup.
    Returns (success: bool, filename: str, detail: str)
    """
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    filename = f"welfare_db_{timestamp}.sql.gz"
    filepath = BACKUP_DIR / filename

    env = os.environ.copy()
    env["PGPASSWORD"] = DB_PASSWORD

    cmd = [
        "pg_dump",
        "-h", DB_HOST,
        "-p", DB_PORT,
        "-U", DB_USER,
        "-d", DB_NAME,
        "--no-owner",
        "--no-acl",
        "-F", "p",  # plain SQL format
    ]

    # Execute pg_dump and pipe through gzip
    try:
        with open(filepath, "wb") as f:
            pg_proc = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                env=env
            )
            gz_proc = subprocess.Popen(
                ["gzip"],
                stdin=pg_proc.stdout,
                stdout=f,
                stderr=subprocess.PIPE
            )
            pg_proc.stdout.close()
            _, gz_err = gz_proc.communicate()
            pg_returncode = pg_proc.wait()

        if pg_returncode != 0:
            stderr = pg_proc.stderr.read().decode() if pg_proc.stderr else "Unknown error"
            filepath.unlink(missing_ok=True)
            return False, filename, stderr

        size_mb = filepath.stat().st_size / (1024 * 1024)
        return True, filename, f"{size_mb:.2f}MB"

    except Exception as e:
        filepath.unlink(missing_ok=True)
        return False, filename, str(e)


def cleanup_old_backups(retention_days: int = RETENTION_DAYS) -> list[str]:
    """
    Delete backup files older than retention_days.
    Returns list of deleted filenames.
    """
    cutoff = datetime.utcnow() - timedelta(days=retention_days)
    deleted = []

    if not BACKUP_DIR.exists():
        return deleted

    for f in BACKUP_DIR.glob("welfare_db_*.sql.gz"):
        try:
            # Extract timestamp from filename: welfare_db_20240101_020000.sql.gz
            ts_str = f.stem.replace("welfare_db_", "").replace(".sql", "")
            file_dt = datetime.strptime(ts_str, "%Y%m%d_%H%M%S")
            if file_dt < cutoff:
                f.unlink()
                deleted.append(f.name)
        except (ValueError, IndexError):
            continue  # Skip files that don't match the pattern

    return deleted


def main():
    """Main backup flow (called from scheduler)"""
    try:
        # 1. Run backup
        success, filename, detail = run_backup()
        if not success:
            raise RuntimeError(f"pg_dump failed: {detail}")

        # 2. Cleanup old backups
        deleted = cleanup_old_backups()

        # 3. Success message
        msg = f"DB backup succeeded: {filename} ({detail})"
        if deleted:
            msg += f"\nDeleted {len(deleted)} old backups: {', '.join(deleted)}"
        print(f"✓ {msg}")
        return True

    except Exception as e:
        error_msg = str(e)
        print(f"❌ DB backup failed: {error_msg}", file=sys.stderr)
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
