"""Background scheduler for data collection tasks"""
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.events import EVENT_JOB_EXECUTED, EVENT_JOB_ERROR
from datetime import datetime
import asyncio
import subprocess
import sys
import os
import httpx
import logging
from pathlib import Path
from app.database import SessionLocal
from app.models import DataCollectionLog
from scripts.backup_db import run_backup, cleanup_old_backups

logger = logging.getLogger(__name__)
scheduler = BackgroundScheduler()


def notify_slack(message: str):
    """Send notification to Slack webhook"""
    slack_webhook = os.getenv("SLACK_WEBHOOK_URL", "")
    if not slack_webhook:
        return

    try:
        httpx.post(
            slack_webhook,
            json={"text": message},
            timeout=5
        )
    except Exception as e:
        print(f"⚠️  Slack notification failed: {e}")


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
            completed_at=datetime.utcnow() if status != "running" else None
        )
        db.add(log)
        db.commit()
    finally:
        db.close()


def run_facility_import():
    """Monthly facility data import (day 1 at 3:00)"""
    script_name = "import_facility_csv"
    csv_path = os.getenv("FACILITY_CSV_PATH", "")

    # Log start
    log_collection(script_name, "running")

    # Validate CSV path
    if not csv_path or not os.path.exists(csv_path):
        error_msg = f"FACILITY_CSV_PATH not set or file not found: {csv_path}"
        log_collection(script_name, "skipped", error_msg=error_msg)
        print(f"⏭️  {error_msg}")
        return

    # Execute with retry logic
    max_retries = 2
    for attempt in range(max_retries):
        try:
            result = subprocess.run(
                [sys.executable, "scripts/import_facility_csv.py", csv_path, "介護"],
                capture_output=True,
                text=True,
                timeout=300
            )

            if result.returncode == 0:
                # Extract record count from output
                records = 0
                for line in result.stdout.split('\n'):
                    if "Imported" in line:
                        try:
                            records = int(line.split()[1])
                        except:
                            pass

                log_collection(script_name, "success", records=records)
                notify_slack(f"✅ Facility import succeeded: {records} records processed")
                print(f"✓ Facility import completed: {records} records")
                return
            else:
                raise Exception(f"Script failed: {result.stderr}")

        except Exception as e:
            error_msg = str(e)
            if attempt < max_retries - 1:
                print(f"⚠️  Facility import attempt {attempt + 1} failed, retrying: {error_msg}")
                continue
            else:
                log_collection(script_name, "failed", error_msg=error_msg)
                notify_slack(f"❌ Facility import failed after {max_retries} retries:\n{error_msg}")
                print(f"❌ Facility import failed: {error_msg}")
                return


def run_daily_backup():
    """Daily database backup (2:00 AM UTC)"""
    script_name = "backup_db"
    log_collection(script_name, "running")

    try:
        # 1. Run backup
        success, filename, detail = run_backup()
        if not success:
            raise RuntimeError(f"pg_dump failed: {detail}")

        # 2. Cleanup old backups
        retention_days = int(os.getenv("BACKUP_RETENTION_DAYS", "7"))
        deleted = cleanup_old_backups(retention_days)

        # 3. Success logging
        log_collection(script_name, "success", records=1)
        msg = f"DB backup succeeded: {filename} ({detail})"
        if deleted:
            msg += f"\nDeleted {len(deleted)} old backups"
        notify_slack(f"✅ {msg}")
        print(f"✓ {msg}")

    except Exception as e:
        error_msg = str(e)
        log_collection(script_name, "failed", error_msg=error_msg)
        notify_slack(f"❌ DB backup failed:\n{error_msg}")
        print(f"❌ DB backup failed: {error_msg}")


def run_financial_import():
    """Annual financial data import (April 1 at 2:00)"""
    script_name = "import_corporation_csv"
    csv_path = os.getenv("FINANCIAL_CSV_PATH", "")

    # Log start
    log_collection(script_name, "running")

    # Validate CSV path
    if not csv_path or not os.path.exists(csv_path):
        error_msg = f"FINANCIAL_CSV_PATH not set or file not found: {csv_path}"
        log_collection(script_name, "skipped", error_msg=error_msg)
        print(f"⏭️  {error_msg}")
        return

    # Execute with retry logic
    max_retries = 2
    for attempt in range(max_retries):
        try:
            result = subprocess.run(
                [sys.executable, "scripts/import_corporation_csv.py", csv_path],
                capture_output=True,
                text=True,
                timeout=300
            )

            if result.returncode == 0:
                # Extract record count from output
                records = 0
                for line in result.stdout.split('\n'):
                    if "Imported" in line or "processed" in line:
                        try:
                            records = int(line.split()[1])
                        except:
                            pass

                log_collection(script_name, "success", records=records)
                notify_slack(f"✅ Financial import succeeded: {records} records processed")
                print(f"✓ Financial import completed: {records} records")
                return
            else:
                raise Exception(f"Script failed: {result.stderr}")

        except Exception as e:
            error_msg = str(e)
            if attempt < max_retries - 1:
                print(f"⚠️  Financial import attempt {attempt + 1} failed, retrying: {error_msg}")
                continue
            else:
                log_collection(script_name, "failed", error_msg=error_msg)
                notify_slack(f"❌ Financial import failed after {max_retries} retries:\n{error_msg}")
                print(f"❌ Financial import failed: {error_msg}")
                return


def scheduler_event_listener(event):
    """Log scheduler job execution events"""
    if event.exception:
        logger.error("scheduler_job_error", extra={
            "job_id": event.job_id,
            "job_name": event.job_name,
            "error": str(event.exception)
        })
    else:
        logger.info("scheduler_job_success", extra={
            "job_id": event.job_id,
            "job_name": event.job_name
        })


def init_scheduler():
    """Initialize background scheduler"""
    # Daily: 2:00 AM UTC (backup)
    scheduler.add_job(
        run_daily_backup,
        CronTrigger(hour=2, minute=0),
        id="daily_backup",
        name="Daily Database Backup"
    )

    # Monthly: every 1st day at 3:00 AM
    scheduler.add_job(
        run_facility_import,
        CronTrigger(day=1, hour=3, minute=0),
        id="facility_import",
        name="Monthly Facility Data Import"
    )

    # Yearly: April 1 at 2:00 AM (Japan fiscal year start)
    scheduler.add_job(
        run_financial_import,
        CronTrigger(month=4, day=1, hour=2, minute=0),
        id="financial_import",
        name="Annual Financial Data Import"
    )

    # Add event listener for job execution logging
    scheduler.add_listener(scheduler_event_listener, EVENT_JOB_EXECUTED | EVENT_JOB_ERROR)

    logger.info("scheduler_initialized", extra={"job_count": 3})


def start_scheduler():
    """Start background scheduler"""
    if not scheduler.running:
        init_scheduler()
        scheduler.start()
        print("✓ Scheduler started")


def stop_scheduler():
    """Stop background scheduler"""
    if scheduler.running:
        scheduler.shutdown(wait=False)
        print("✓ Scheduler stopped")
