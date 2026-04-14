"""System monitoring and metrics endpoint"""
from fastapi import APIRouter
from datetime import datetime
from pathlib import Path
import os
import resource
from typing import Optional

router = APIRouter(prefix="/api/monitoring", tags=["monitoring"])


class BackupFile:
    def __init__(self, path: Path):
        self.filename = path.name
        stat = path.stat()
        self.size_bytes = stat.st_size
        self.created_at = datetime.utcfromtimestamp(stat.st_mtime).isoformat()

    def to_dict(self):
        return {
            "filename": self.filename,
            "size_bytes": self.size_bytes,
            "created_at": self.created_at,
        }


@router.get("/metrics")
def get_system_metrics():
    """
    Get system monitoring metrics.
    Returns memory usage, backup file info, and monitoring service URLs.
    """
    # Get memory RSS (maximum resident set size) in MB
    mem = resource.getrusage(resource.RUSAGE_SELF)
    memory_rss_mb = round(mem.ru_maxrss / 1024, 2)  # Linux: KB to MB

    # Get backup files (latest 5)
    backup_dir = os.getenv("BACKUP_DIR", "/backups")
    backups = []
    backup_path = Path(backup_dir)
    if backup_path.exists():
        files = sorted(backup_path.glob("welfare_db_*.sql.gz"), reverse=True)[:5]
        backups = [BackupFile(f).to_dict() for f in files]

    return {
        "timestamp": datetime.utcnow().isoformat(),
        "memory_rss_mb": memory_rss_mb,
        "uptime_seconds": None,  # Can be calculated from app startup time if needed
        "backup_files": backups,
        "latest_backup": backups[0] if backups else None,
        "prometheus_url": "http://localhost:9091",
        "grafana_url": "http://localhost:3002",
    }
